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

> Preencha esta parte com os **números das execuções** (Actions → execução → número `#N` / URL) e os prints em `evidencias/`.
> Cada linha diz o que executar e qual resultado comprova o critério.

### Cenário 1 · Criação inicial (ACE-01, ACE-02)
Pipeline **2**: `environment=dev`, `instance_type=t3.micro`, `db_instance_type=t3.small`, `docker_tag=1.0.0`, `update_os=true`, `extra_packages=htop`.

| Verificação | Resultado esperado | Execução / resultado |
|---|---|---|
| Imagens 1.0.0 construídas pelo CI/CD da aplicação | job "Construir imagens ausentes" verde | |
| Terraform plan | `Plan: N to add, 0 to change, 0 to destroy` | |
| Terraform apply | `Apply complete!` + inventário com 2 VMs (db sem IP público) | |
| Ansible | `failed=0`, `changed>0` nos dois hosts | |
| Smoke pela internet | `SMOKE_RESULT=PASS` | |
| Isolamento | `ISOLATION_RESULT=PASS` + "Mongo sem senha: RECUSADO" | |
| Loja no navegador (ACE-04) | catálogo, pedido criado, visível depois de F5 em *Meus pedidos* | |

### Cenário 2 · Atualização (ACE-05)
Pipeline **2** com `instance_type=t3.small`, `docker_tag=1.1.0`, `extra_packages=htop, tree`, `update_os=false`.

| Verificação | Resultado esperado | Execução / resultado |
|---|---|---|
| Terraform (infra) | `Plan: 0 to add, 1 to change, 0 to destroy` (`~ instance_type`, sem recriar) | |
| Ansible (manutenção) | pacote `tree` instalado, imagens 1.1.0 baixadas e contêineres recriados (`changed>0`) | |
| Nova versão | `GET /api/info` → `"version":"1.1.0"` | |
| Persistência | pedido do Cenário 1 continua em *Meus pedidos* | |

### Cenário 3 · Reexecução sem alterações
Pipeline **2** com os mesmos parâmetros do Cenário 2.

| Verificação | Resultado esperado | Execução / resultado |
|---|---|---|
| Terraform | `No changes. Your infrastructure matches the configuration.` | |
| Ansible | `changed=0` em todos os hosts ("Idempotente") | |

### Operação e recuperação (ACE-05, ACE-07, ACE-08)

| Passo (pipeline 3) | Resultado esperado | Execução / resultado |
|---|---|---|
| `health` | `failed=0`, banco healthy, 27017 só no IP privado, timer de backup ativo | |
| `restart` (`service=all`) | contêineres healthy, mesma quantidade de pedidos (persistência após reinício) | |
| `backup` | `BACKUP_OK key=dev/… orders=N` | |
| criar 1 pedido na loja | histórico com N+1 | |
| `list-backups` | tabela com a chave e `orders=N` | |
| `restore` (`latest`, `RESTAURAR`) | `RESTORE_OK … pedidos_backup=N pedidos_depois=N` | |
| backup automático | `logs service=backup` mostra a execução diária do timer (no dia seguinte) | |
| `logs` | logs JSON da API e do MongoDB sem credenciais | |

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
