"""Instala a aplicacao nas quatro EC2 existentes, por SSH, sem criar maquinas."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def checked(command, **kwargs):
    result = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8", **kwargs)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command[0]}\n{result.stderr}\n{result.stdout}")
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", type=Path, required=True, help="Caminho local da chave; o conteudo nao e lido pelo script")
    args = parser.parse_args()
    inventory = json.loads((ROOT / "deployment/inventory.json").read_text(encoding="utf-8"))
    machines = inventory["machines"]
    naming = f"{machines[0]['private_ip']}:{machines[0]['port']}"
    known_hosts = str(ROOT / "deployment/known_hosts")
    ssh_options = ["-i", str(args.key.resolve()), "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "StrictHostKeyChecking=accept-new", "-o", f"UserKnownHostsFile={known_hosts}"]

    def remote(machine, command):
        return checked(["ssh", *ssh_options, f"ubuntu@{machine['public_ip']}", command], timeout=360)

    def preflight(machine):
        output = remote(machine, "set -eu; test ! -d /home/ubuntu/sd-grpc || test -f /home/ubuntu/sd-grpc/.sd-grpc-managed; hostname; python3 --version; sudo -n true")
        print(f"SSH OK: {machine['name']} {output.strip()}", flush=True)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(preflight, machines))

    aws_exe = shutil.which("aws") or str(Path(os.environ["LOCALAPPDATA"]) / "Programs/Amazon/AWSCLIV2/aws.exe")
    aws_env = os.environ.copy()
    aws_env.update(AWS_PAGER="", AWS_CLI_OUTPUT_ENCODING="UTF-8")

    def aws(*arguments):
        return checked([aws_exe, *arguments, "--profile", inventory['profile'], "--region", inventory['region'], "--no-cli-pager"], env=aws_env, timeout=60)

    group_id = inventory['security_group']
    group = json.loads(aws("ec2", "describe-security-groups", "--group-ids", group_id))["SecurityGroups"][0]
    matching = any(rule.get('IpProtocol') == 'tcp' and rule.get('FromPort') == 50061 and rule.get('ToPort') == 50063 and any(pair['GroupId'] == group_id for pair in rule.get('UserIdGroupPairs', [])) for rule in group['IpPermissions'])
    if not matching:
        rule = [{"IpProtocol": "tcp", "FromPort": 50061, "ToPort": 50063, "UserIdGroupPairs": [{"GroupId": group_id, "Description": "SD gRPC between lab instances only"}]}]
        rule_path = ROOT / 'deployment/grpc-ingress.json'
        rule_path.write_text(json.dumps(rule), encoding='utf-8')
        aws("ec2", "authorize-security-group-ingress", "--group-id", group_id, "--ip-permissions", "file://" + rule_path.as_posix())
    print("Private gRPC network rule OK.", flush=True)

    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    bundle = dist / 'sd-grpc.tar.gz'
    allowed = ('sdgrpc', 'protos', 'tests', 'tools', 'deployment/install.sh', 'requirements.txt', 'requirements.in', 'README.md')

    def archive_filter(info):
        return None if '__pycache__' in info.name or info.name.endswith('.pyc') else info

    with tarfile.open(bundle, 'w:gz') as archive:
        for name in allowed:
            archive.add(ROOT / name, arcname=name, filter=archive_filter)
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    remote_bundle = f"/home/ubuntu/sd-grpc-{digest[:12]}.tar.gz"

    def install(machine):
        checked(["scp", *ssh_options, str(bundle), f"ubuntu@{machine['public_ip']}:{remote_bundle}"], timeout=60)
        command = (
            "set -eu; "
            f"printf '%s  %s\\n' {shlex.quote(digest)} {shlex.quote(remote_bundle)} | sha256sum -c -; "
            "mkdir -p /home/ubuntu/sd-grpc; touch /home/ubuntu/sd-grpc/.sd-grpc-managed; "
            f"tar -xzf {shlex.quote(remote_bundle)} -C /home/ubuntu/sd-grpc; "
            f"bash /home/ubuntu/sd-grpc/deployment/install.sh {shlex.quote(machine['role'])} {shlex.quote(machine['private_ip'])} {machine['port']} {shlex.quote(naming)}; "
            f"rm -- {shlex.quote(remote_bundle)}"
        )
        output = remote(machine, command)
        print(f"INSTALLED: {machine['name']} ({machine['role']})\n{output[-1500:]}", flush=True)

    install(machines[0])
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(install, machines[1:]))
    evidence = remote(machines[3], f"cd /home/ubuntu/sd-grpc && .venv/bin/python tools/verify_live.py --naming {shlex.quote(naming)}")
    result = json.loads(evidence)
    result['verified_at_utc'] = datetime.now(timezone.utc).isoformat()
    result['source_archive_sha256'] = digest
    result['deployment'] = machines
    (ROOT / 'deployment/evidencia-remota.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
