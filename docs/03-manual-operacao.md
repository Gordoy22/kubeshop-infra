# 03 · Manual de operação (equipe Zibiska Korp)

Todas as rotinas rodam pelo GitHub: **Actions → escolher o pipeline → Run workflow**.
Cada execução deixa um **resumo** (aba *Summary*) e **artefatos** (logs completos) por 90 dias. Nenhuma credencial aparece neles.

> **Rotinas do dia a dia** (pipelines 2 e 3, exceto restore) não removem dados.
> **Rotinas destrutivas** pedem confirmação digitada: `restore` (substitui pedidos) e o pipeline **9 · Desativar** (remove recursos).

---

## Rotinas do dia a dia

### Implantar / atualizar o ambiente: pipeline 2
| Parâmetro | Quando mudar |
|---|---|
| `run_mode=plan` | para **só ver** o que mudaria (nada é aplicado) |
| `instance_type` / `db_instance_type` | mais/menos capacidade. Causa uma breve parada da VM alterada (stop/start). |
| `db_volume_gb` | disco do banco perto de encher (só aumenta, online) |
| `docker_tag` | nova versão da aplicação (constrói automaticamente se não existir) |
| `update_os=true` | janela de manutenção do SO (reinicia só se necessário) |
| `extra_packages` | instalar ferramentas (ex.: `htop, tree`) |

**Resultado esperado:** jobs verdes, *Terraform plan* com o que mudou, *PLAY RECAP* com `failed=0`, *Testes* com `SMOKE_RESULT=PASS` e `ISOLATION_RESULT=PASS`.

### Consulta de saúde: pipeline 3, `action=health`
Mostra o estado do Docker e dos contêineres, a loja, `/api/health/ready`, o catálogo, a conexão privada ao banco, a recusa sem senha,
a porta 27017 só no IP privado, o volume de dados, a quantidade de pedidos, o timer de backup e CPU/memória/disco.
**Esperado:** `failed=0` e o resumo com os itens OK.

### Teste funcional completo: `action=smoke-test`
Cria **1 pedido fictício** e confirma que ele aparece no histórico. Esperado: `SMOKE_RESULT=PASS`.

### Logs / diagnóstico: `action=logs`
`service` = `all` | `frontend` | `api` | `mongodb` | `backup`, e `log_lines` (padrão 200). O log completo fica no artefato `ops-logs-…`.
A API registra uma linha JSON por requisição (`requestId`, rota, status e duração) e `database_retry` quando não alcança o banco.

### Reinício: `action=restart`
`service=all` reinicia na ordem segura: banco → API → frontend, esperando cada um ficar *healthy*. Os pedidos ficam preservados no volume EBS.

### Backup sob demanda: `action=backup`
O mesmo script do **backup automático diário (03:00 UTC)**, que roda por *systemd timer* na VM do banco.
**Esperado:** `BACKUP_OK key=dev/kubeshop-dev-AAAAMMDDTHHMMSSZ.archive.gz orders=N sha256=…`.
O backup é um `mongodump --gzip` do banco `kubeshop` mais um `.json` de metadados (pedidos e SHA-256).
Fica no S3 `kubeshop-backups-<conta>-<região>/<ambiente>/`, com retenção de **30 dias** e versionamento. Também há uma cópia local de 3 dias em `/var/backups/kubeshop`.

### Listar backups: `action=list-backups`
Tabela com a chave (para usar no restore), a quantidade de pedidos, o tamanho e o SHA-256.

### Atualizar só a aplicação: `action=deploy-app`
Troca os contêineres para `docker_tag` sem rodar o Terraform. É usado pelo pipeline **1 · App CI/CD** (`deploy_environment`).

---

## Rotinas destrutivas

### Restaurar: `action=restore`
Parâmetros: `backup_key` (`latest` ou uma chave da listagem) e **`confirm=RESTAURAR`**.
Etapas: baixa o backup → confere o **SHA-256** → `mongorestore --drop` (substitui os pedidos atuais) → **confere se a quantidade de pedidos é igual à do backup** → verifica a aplicação.
**Esperado:** `RESTORE_OK key=… sha256=OK pedidos_antes=X pedidos_backup=N pedidos_depois=N`.
Antes de restaurar em produção, faça um `backup` para poder voltar ao estado atual.

<a id="desativar"></a>
### Desativar o ambiente: pipeline 9
Parâmetros: `environment` e **`confirmation=DESTRUIR-<ambiente>`**, `final_backup` (padrão: sim) e `remove_backup_bucket` (padrão: não).

| Item | Destino |
|---|---|
| VMs, EIP, VPC, sub-redes, rotas, SGs, endpoint, IAM, key pair | **removidos** |
| Volume EBS com os pedidos | **removido**. Os dados ficam apenas no backup final do S3. |
| Bucket de backups (todos os ambientes) | **mantido** (expira os objetos em 30 dias), salvo `remove_backup_bucket=true` |
| Bucket do Terraform State | **mantido** (centavos/mês). Permite recriar o ambiente. |
| Imagens no GHCR | mantidas (gratuitas em repositório público) |
| **Custo que continua** | apenas o S3: **< US$ 0,10/mês** |

**Recriar depois:** pipeline 2 (mesmos parâmetros) e depois pipeline 3 → `restore` com `backup_key=latest`.

---

<a id="recuperação-de-falhas"></a>
## Recuperação de falhas

| Situação | O que fazer |
|---|---|
| Pipeline falhou no **Terraform plan** | Ler o erro no log. Normalmente é parâmetro inválido, cota ou credencial. Nada foi alterado. Corrigir e reexecutar. |
| Pipeline falhou **durante o apply** | O state registra o que foi criado. **Reexecutar** a pipeline completa, que é idempotente e termina o que faltou. |
| `Error acquiring the state lock` | Outra execução está rodando (espere). Se ela foi cancelada, use `terraform force-unlock <ID>` localmente com as credenciais, ou apague o arquivo `.tflock` no bucket de state. |
| State corrompido ou sobrescrito | O bucket é **versionado**: restaure a versão anterior do objeto `kubeshop/<amb>/terraform.tfstate` (console S3 → *Show versions*). |
| Falha no **Ansible** | O log indica a task. Reexecutar: só o que falta é aplicado. `UNREACHABLE` logo após criar as VMs costuma ser boot em andamento. |
| Versão nova da aplicação com problema | **Reverter:** pipeline 2 (ou 3 → `deploy-app`) com o `docker_tag` anterior. |
| Loja abre mas mostra "Serviço indisponível" | `health` → se `database=false`: `logs service=mongodb`, depois `restart service=mongodb`. |
| Pedidos apagados ou corrompidos | `list-backups` → `restore` com a chave anterior ao problema. |
| VM do banco perdida | Pipeline 2 recria a VM e reanexa o mesmo volume EBS (dados preservados). Se o volume também foi perdido: pipeline 2 e depois `restore`. |
| Disco do banco cheio | Pipeline 2 com `db_volume_gb` maior (ampliação online). |
| Backup diário não rodou | `logs service=backup` (mostra o journal do timer) e depois `backup` manual. |

## Identificação dos recursos na AWS

Todos os recursos têm as tags `Project=KubeShop`, `Environment=<amb>` e `ManagedBy=Terraform`.
No console: **Resource Groups & Tag Editor → Project = KubeShop**. Os nomes seguem o padrão `<instance_name>-<ambiente>-<função>`.
Não altere esses recursos pelo console: a próxima execução da pipeline reverteria a mudança ou mostraria *drift* no plan.
