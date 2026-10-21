#!/usr/bin/env bash
set -euo pipefail
role="$1"
listen_ip="$2"
port="$3"
naming="$4"
project="$HOME/sd-grpc"
cd "$project"
mkdir -p var
if [ ! -x "$HOME/.local/bin/uv" ]; then
    stage="$(mktemp -d)"
    curl --fail --silent --show-error --location --retry 3 https://astral.sh/uv/install.sh -o "$stage/install-uv.sh"
    UV_NO_MODIFY_PATH=1 sh "$stage/install-uv.sh"
fi
uv="$HOME/.local/bin/uv"
if [ ! -x .venv/bin/python ]; then
    "$uv" venv --python /usr/bin/python3 .venv
fi
"$uv" pip install --python .venv/bin/python -r requirements.txt
if [ "$role" = client ]; then
    printf '#!/usr/bin/env bash\nset -euo pipefail\ncd "%s"\nexec .venv/bin/python -m sdgrpc.client --naming "%s" "$@"\n' "$project" "$naming" > run-client.sh
    chmod 750 run-client.sh
    echo 'CLIENT_READY'
    exit 0
fi
service="sd-grpc-$role"
arguments="$role --listen-host $listen_ip --port $port"
if [ "$role" = names ]; then
    arguments="$arguments --database $project/var/names.sqlite3"
else
    arguments="$arguments --naming $naming --advertise-host $listen_ip"
fi
unit="$(mktemp)"
cat > "$unit" <<EOF
[Unit]
Description=SD gRPC $role
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$project
ExecStart=$project/.venv/bin/python -m sdgrpc.server $arguments
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONDONTWRITEBYTECODE=1
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$project/var
UMask=0077

[Install]
WantedBy=multi-user.target
EOF
sudo install -m 644 "$unit" "/etc/systemd/system/$service.service"
sudo systemctl daemon-reload
sudo systemctl enable "$service.service"
sudo systemctl restart "$service.service"
sudo systemctl is-active "$service.service"
