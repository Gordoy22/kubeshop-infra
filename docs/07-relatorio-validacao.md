# 07 · Relatório de validação

## Parte A · Validação estática do código (executada em 25/11/2026)

Feita na máquina de desenvolvimento (Windows 11) antes do primeiro envio ao GitHub. O pipeline **0 · CI** repete
estas verificações automaticamente a cada push e acrescenta `ansible-playbook --syntax-check`, `ansible-lint` e `gitleaks`,
que só rodam em Linux.

| Verificação | Ferramenta | Resultado |
|---|---|---|
| Formatação do Terraform (2 stacks) | `terraform fmt -check -recursive` (Terraform 1.17.2) | **PASS**, nenhuma diferença |
| Validação do Terraform (global e environment) | `terraform init -backend=false` + `terraform validate` (provider aws ~> 6.0) | **PASS**, "The configuration is valid" |
| Workflows do GitHub Actions (5 workflows + 2 ações) | `actionlint` (com shellcheck integrado) | **PASS**, 0 problemas |
| Scripts bash (8 scripts) | `shellcheck -S warning` | **PASS**, 0 avisos |
| YAML de Ansible e workflows | `yamllint` (regras compatíveis com ansible-lint) + parse de todos os YAML | **PASS** |
| Scripts PowerShell | parser do PowerShell + verificação ASCII | **PASS** |
| Código da aplicação | análise do repositório `kube-shop-v2@ee30950` (compose, Dockerfiles, nginx.conf, config da API) | adaptação para dois hosts documentada no doc 01 §1 |

## Parte B · Validação na nuvem (cenários do PM-04 e critérios de aceite)

Conta AWS no plano Free, região **us-east-2**. As duas primeiras execuções do pipeline 2 pararam **antes de criar qualquer recurso**:
- a primeira esbarrou na restrição de região do plano Free, que só libera a us-east-2 (diagnosticada pelo pipeline **8 · Diagnóstico**);
- a segunda esbarrou numa tag com caracteres inválidos no bucket de backups, corrigida no commit seguinte.

A partir daí as execuções abaixo rodaram limpas.

> Preencha esta parte com os **números das execuções** (Actions → execução → número `#N` / URL) e os prints em `evidencias/`.
> Cada linha diz o que executar e qual resultado comprova o critério.

### Cenário 1 · Criação inicial (ACE-01, ACE-02)
Pipeline **2**: `environment=dev`, `instance_type=t3.micro`, `db_instance_type=t3.small`, `docker_tag=1.0.0`, `update_os=true`, `extra_packages=htop`.

| Verificação | Resultado esperado | Execução / resultado |
|---|---|---|
| Imagens 1.0.0 construídas pelo CI/CD da aplicação | job "Construir imagens ausentes" verde | ✅ [run 45869148123](https://github.com/Gordoy22/kubeshop-infra/actions/runs/45869148123): testes da aplicação + build e publicação de api/frontend no GHCR |
| Terraform plan | `Plan: N to add, 0 to change, 0 to destroy` | ✅ [run 45870323873](https://github.com/Gordoy22/kubeshop-infra/actions/runs/45870323873): `Plan: 32 to add, 0 to change, 0 to destroy` |
| Terraform apply | `Apply complete!` + inventário com 2 VMs (db sem IP público) | ✅ `Apply complete! Resources: 32 added`. `kubeshop-dev-app` (t3.micro, Elastic IP) e `kubeshop-dev-db` (t3.small, 10.20.2.10, **sem IP público**) |
| Ansible | `failed=0`, `changed>0` nos dois hosts | ✅ app `ok=62 changed=27 failed=0` · db `ok=73 changed=32 failed=0` (Docker 29.10.1, mongo:8.0.17, volume de 10 GiB montado, timer de backup ativo) |
| Smoke pela internet | `SMOKE_RESULT=PASS` | ✅ HTML da loja, `{"ready":true,"database":true}`, 6 produtos, rotas inexistentes respondendo 404 |
| Isolamento | `ISOLATION_RESULT=PASS` + "Mongo sem senha: RECUSADO" | ✅ banco sem IP público; 27017 fechada pela internet; SG do banco aceita só o SG da aplicação; `RECUSADO:Unauthorized`; escuta só em 10.20.2.10 |
| Loja no navegador (ACE-04) | catálogo, pedido criado, visível depois de F5 em *Meus pedidos* | |

### Cenário 2 · Atualização (ACE-05)
Pipeline **2** com `instance_type=t3.small`, `docker_tag=1.1.0`, `extra_packages=htop, tree`, `update_os=false`.

| Verificação | Resultado esperado | Execução / resultado |
|---|---|---|
| Terraform (infra) | `Plan: 0 to add, 1 to change, 0 to destroy` (`~ instance_type`, sem recriar) | ✅ [run 45874087005](https://github.com/Gordoy22/kubeshop-infra/actions/runs/45874087005): `aws_instance.app will be updated in-place`, `~ instance_type = "t3.micro" -> "t3.small"`, `Plan: 0 to add, 1 to change, 0 to destroy`, `Apply complete! Resources: 0 added, 1 changed, 0 destroyed` |
| Ansible (manutenção) | pacote `tree` instalado, imagens 1.1.0 baixadas e contêineres recriados (`changed>0`) | ✅ app `changed=6`: pacotes (`htop, tree`), login→pull 1.1.0→logout no GHCR, API e frontend recriados · db `changed=1` · `failed=0`. Imagens 1.1.0 construídas antes pelo CI/CD da aplicação. |
| Nova versão | `GET /api/info` → `"version":"1.1.0"` | ✅ antes `{"version":"1.0.0"}` → depois `{"version":"1.1.0"}` |
| Persistência | pedido do Cenário 1 continua em *Meus pedidos* | ✅ pedido `…11ed462` (Monitor Horizon, R$ 899,90) presente antes e depois; "Pedidos persistidos: 1" |

### Cenário 3 · Reexecução sem alterações
Pipeline **2** com os mesmos parâmetros do Cenário 2.

| Verificação | Resultado esperado | Execução / resultado |
|---|---|---|
| Terraform | `No changes. Your infrastructure matches the configuration.` | ✅ [run 45874953922](https://github.com/Gordoy22/kubeshop-infra/actions/runs/45874953922): `No changes. Your infrastructure matches the configuration.` |
| Ansible | `changed=0` em todos os hosts ("Idempotente") | ✅ app `ok=52 changed=0 failed=0` · db `ok=65 changed=0 failed=0` |

### Operação e recuperação (ACE-05, ACE-07, ACE-08)

| Passo (pipeline 3) | Resultado esperado | Execução / resultado |
|---|---|---|
| `health` | `failed=0`, banco healthy, 27017 só no IP privado, timer de backup ativo | ✅ [run 45875471275](https://github.com/Gordoy22/kubeshop-infra/actions/runs/45875471275): `RECUSADO:Unauthorized`, pedidos persistidos 1, timer `active` |
| `restart` (`service=all`) | contêineres healthy, mesma quantidade de pedidos (persistência após reinício) | ✅ [run 45875661419](https://github.com/Gordoy22/kubeshop-infra/actions/runs/45875661419): banco → API → frontend reiniciados, pedidos persistidos 1 (o mesmo pedido de antes) |
| `backup` | `BACKUP_OK key=dev/… orders=N` | ✅ [run 45875935548](https://github.com/Gordoy22/kubeshop-infra/actions/runs/45875935548): `BACKUP_OK key=dev/kubeshop-dev-20261126T182734Z.archive.gz orders=1 bytes=492 sha256=8593120f…` |
| criar 1 pedido na loja | histórico com N+1 | ✅ [run 45876148765](https://github.com/Gordoy22/kubeshop-infra/actions/runs/45876148765) (`smoke-test`): `POST /api/orders -> 201` pedido `…7a518d54`; histórico passou a ter 2 pedidos |
| `list-backups` | tabela com a chave e `orders=N` | ✅ [run 45876254224](https://github.com/Gordoy22/kubeshop-infra/actions/runs/45876254224): `dev/kubeshop-dev-20261126T182734Z.archive.gz` · 1 pedido · 492 B |
| `restore` (`latest`, `RESTAURAR`) | `RESTORE_OK … pedidos_backup=N pedidos_depois=N` | ✅ [run 45876364892](https://github.com/Gordoy22/kubeshop-infra/actions/runs/45876364892): `RESTORE_OK … sha256=OK pedidos_antes=2 pedidos_backup=1 pedidos_depois=1`. Na loja sobrou só o pedido `…11ed462`. |
| backup automático | `logs service=backup` mostra a execução diária do timer (no dia seguinte) | ⏳ timer ativo (próxima execução às 03:00 UTC). Conferir com `logs service=backup` no dia 27/11. |
| `logs` | logs JSON da API e do MongoDB sem credenciais | ⏳ executar antes da apresentação |

### Desativação

| Passo | Resultado esperado | Execução / resultado |
|---|---|---|
| Pipeline **9** (`DESTRUIR-dev`) | backup final `BACKUP_OK`, `Destroy complete! Resources: N destroyed`, relatório do que permanece | |

## Credenciais fora do código e dos logs (REQ-04, ACE-08)

- `gitleaks` no CI: nenhum segredo no histórico do Git.
- Logs das execuções: valores de secrets aparecem como `***`. Tarefas com senha aparecem como `censored due to no_log`.
- `docker inspect` nas VMs mostra apenas `*_PASSWORD_FILE=/run/secrets/…`, sem senhas.
- O state do Terraform não contém senhas (as senhas do banco não passam pelo Terraform).

## Conclusão

A Parte A comprova que o código está sintaticamente válido e consistente. A Parte B é executada pelos pipelines na conta AWS
do projeto, e seus registros (números das execuções, resumos e artefatos de 90 dias) formam a evidência verificável exigida
pelos critérios ACE-01 a ACE-08 e pelos Cenários 1 a 3 do PM-04.
