# 04 · Integração com o CI/CD da aplicação (ACE-06)

## Divisão de responsabilidades

| Fluxo | Pipeline | Responsável | Faz | Não faz |
|---|---|---|---|---|
| CI/CD da aplicação | **1 · App CI/CD** (`app-cicd.yml`) | Zibiska Korp (capacidade existente) | testes (`npm test`), build com os Dockerfiles originais, publicação no GHCR, deploy da tag (opcional) | não altera infraestrutura nem banco |
| Infraestrutura | **2 · Infra** (`infra-deploy.yml`) | Profissional de infra | Terraform + Ansible completos, testes, evidências | não altera o código da aplicação |
| Operação | **3 · Operação** (`ops.yml`) | Equipe do cliente | saúde, logs, reinício, backup, restauração, deploy de tag | não cria nem remove recursos |
| Desativação | **9 · Desativar** (`destroy.yml`) | Equipe do cliente (com confirmação) | backup final + `terraform destroy` | não apaga backups (salvo opção explícita) |

## Pontos de integração

| Ponto | Valor | Onde configurar |
|---|---|---|
| Repositório da aplicação | `LaercioMLB/kube-shop-v2` | variável do repositório `APP_REPOSITORY` |
| Versão do código | commit/branch/tag (`app_ref`). Padrão: `ee30950…` (validado) | input do pipeline 1 |
| Registro de imagens (destino do build) | `ghcr.io/<dono-do-repo>/kubeshop-api:<tag>` e `…/kubeshop-frontend:<tag>` | automático (`GITHUB_REPOSITORY_OWNER`) |
| Contrato de deploy | **a infraestrutura consome `<docker_image>-api:<docker_tag>` e `<docker_image>-frontend:<docker_tag>`** | inputs `docker_image` e `docker_tag` (pipelines 2 e 3) |
| Destino de implantação | VM `kubeshop-<amb>-app`, contêineres `api` e `frontend`, porta 80 | output `store_url` do Terraform |
| Disparo do deploy pelo CI/CD da aplicação | pipeline 1 com `deploy_environment=dev|homolog|prod` chama `ops.yml` (`action=deploy-app`) | input do pipeline 1 |
| Build automático | o pipeline 2 detecta tag inexistente no GHCR e chama o pipeline 1 (`workflow_call`) | automático |
| Configuração de runtime injetada pela infra | `MONGO_HOST` (IP privado do banco), `MONGO_USERNAME`, `MONGO_PASSWORD_FILE`, `MONGO_DATABASE`, `MONGO_AUTH_SOURCE`, `APP_VERSION=<tag>` | `ansible/roles/containers` |
| Verificação pós-deploy | `GET /api/health/ready` (inclui banco), `GET /`, `GET /api/products` | `ansible/roles/verify` e `scripts/smoke.sh` |

Se a Zibiska usar outro CI (GitLab, Jenkins), basta publicar as imagens com essa convenção de nomes em um registro acessível e
chamar o pipeline 3 (`deploy-app`) pela API do GitHub:
`gh workflow run ops.yml -f environment=prod -f action=deploy-app -f docker_tag=1.2.0 -f docker_image=registry.exemplo.com/zibiska/kubeshop`.
Para registros privados de terceiros, informe as credenciais de leitura (`REGISTRY_USERNAME`/`REGISTRY_PASSWORD`) como secrets.

## Segredos e variáveis (somente referências, sem valores)

| Nome | Tipo | Usado por | Finalidade |
|---|---|---|---|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Secret | 2, 3, 9 | credencial do usuário IAM da pipeline |
| `AWS_ROLE_ARN` | Secret (opcional) | 2, 3, 9 | alternativa OIDC sem chave fixa (tem prioridade) |
| `SSH_PRIVATE_KEY` | Secret | 2, 3, 9 | acesso administrativo às VMs. A chave pública é derivada dela e vai ao Terraform. |
| `MONGO_ROOT_PASSWORD` | Secret | 2, 3 | usuário administrador do MongoDB (backup/restore) |
| `MONGO_APP_PASSWORD` | Secret | 2, 3 | usuário `kubeshop` usado pela API |
| `GITHUB_TOKEN` | automático | 1, 2, 3 | publicar (pipeline 1) e baixar (VM, temporário) imagens do GHCR |
| `AWS_REGION` | Variável | todos | região (padrão `us-east-1`) |
| `APP_REPOSITORY` | Variável | 1 | repositório do código da aplicação |
| `ADMIN_CIDRS` | Variável (opcional) | 2 | SSH permanente para IPs da equipe, em formato HCL: `["200.1.2.3/32"]` |
| `TF_STATE_BUCKET` | Variável (opcional) | 2, 3, 9 | nome do bucket de state, se quiser um nome próprio |

**Como os segredos são protegidos:** ficam só em GitHub Secrets e são mascarados nos logs. As tarefas do Ansible com senha usam `no_log`.
As senhas chegam ao Ansible por variável de ambiente (nunca pela linha de comando) e, nas VMs, ficam em arquivos `0400` montados nos contêineres.
O token do GHCR é usado só durante o pull, com `docker logout` logo depois.
