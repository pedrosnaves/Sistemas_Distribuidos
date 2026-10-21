# Relatório de implementação e validação

Data: 21/10/2026. Ambiente: quatro EC2 existentes do AWS Academy Learner Lab, Ubuntu 26.04, região `us-east-1`.

## Atendimento ao enunciado

| Requisito | Implementação | Validação |
| --- | --- | --- |
| Dois serviços de aplicação remotos | CalculatorService e TextService | Cliente fez RPCs para duas máquinas distintas |
| Processos e máquinas diferentes | Server-01 nomes; Server-02 cálculo; Server-03 texto; Server-04 cliente | Hostnames, IPs e PIDs registrados na evidência |
| Cliente com requisições | `sdgrpc/client.py` | Soma 12 + 3 = 15 e análise de texto com 30 caracteres e 4 palavras |
| Descoberta dos endereços | Lookup antes de cada RPC de aplicação | Cliente possui apenas o bootstrap do Serviço de Nomes |
| bind | Inserção de nome único em SQLite | Registro e busca pela rede; duplicata recusada sem substituir endereço |
| lookup | Consulta por nome | Endereço correto; NOT_FOUND após remoção |
| unbind | Remoção transacional | Nome removido e busca posterior recusada |
| rebind | Atualização do endereço, ou criação caso ausente | Endereço atualizado e nova descoberta pelo cliente |
| gRPC em todos os servidores | Contratos Protobuf e stubs gerados pelo grpcio-tools | Chamadas reais gRPC, sem HTTP/JSON substituindo o protocolo |

## Estado verificado na implantação

| Máquina | Programa | PID observado | Endereço |
| --- | --- | --- | --- |
| Server-01 | Serviço de Nomes | 1941 | 172.31.65.237:50061 |
| Server-02 | Calculadora | 1716 | 172.31.68.163:50062 |
| Server-03 | Texto | 27328 | 172.31.64.70:50063 |
| Server-04 | Cliente da demonstração | 27325 | execução sob demanda |

Os PIDs são evidência de uma execução e podem mudar ao reiniciar. Os três servidores estavam `active/running` no systemd e escutavam somente no respectivo endereço privado. O cliente encerra após receber as respostas; pode ser executado novamente com `./run-client.sh demo` na Server-04.

## Evidências

- [Resultado das requisições e operações de nomes entre EC2](deployment/evidencia-remota.json).
- [Estado do Serviço de Nomes](deployment/status-Server-01.txt).
- [Estado da calculadora](deployment/status-Server-02.txt).
- [Estado do serviço de texto](deployment/status-Server-03.txt).
- [Testes executados na Server-04](deployment/testes-ec2.txt).

Os 11 testes locais passaram, incluindo concorrência de 20 registros para o mesmo nome, persistência após reinicialização do registro, descoberta após rebind, as quatro operações aritméticas, erros e Unicode. A demonstração local confirmou quatro PIDs distintos e encerrou os servidores de forma controlada. Na implantação, `verify_live.py` registrou um nome de teste exclusivo, validou as quatro operações e removeu o registro ao terminar.

## Alterações no ambiente

- Aplicação em `/home/ubuntu/sd-grpc` nas quatro máquinas, com ambiente virtual próprio.
- Três unidades systemd: `sd-grpc-names`, `sd-grpc-calculator`, `sd-grpc-text`.
- Regra TCP 50061–50063 no security group `sg-0b3cb1ddb3bf9299a`, com origem no próprio grupo. As regras anteriores foram preservadas.
- Nenhuma EC2 nova foi criada, e nenhuma instância foi parada ou encerrada.
- A chave SSH existente foi utilizada através de uma cópia local com permissões restritas em `C:\Users\Pedro\.ssh\sd-grpc-lab.pem`. Ela não foi incluída no projeto nem enviada às instâncias.

## Limitações

O Serviço de Nomes é centralizado e não possui replicação nem detecção automática de serviços mortos. O transporte sem TLS é uma escolha didática restrita à rede privada; não há autenticação de registros. O procedimento de execução, decisões de semântica e comandos de administração estão no [README](README.md).
