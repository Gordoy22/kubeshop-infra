# 00 · Passo a passo: do zero até a loja no ar

Tempo total estimado: **cerca de 40 minutos**. São 15 de cadastro e 25 da pipeline rodando sozinha.

## O que depende de você (não pode ser automatizado)

| # | Ação | Por quê |
|---|---|---|
| 1 | Criar a **conta AWS** e informar um cartão | Exigência da AWS. Contas novas recebem créditos do plano gratuito. |
| 2 | Criar o **usuário IAM** `kubeshop-pipeline` e a **access key** | A pipeline precisa de credenciais. Só você pode emiti-las. |
| 3 | Ter uma **conta GitHub** e autorizar o GitHub CLI no navegador | O login é pessoal. |
| 4 | Colar a access key quando o script pedir | Credenciais são digitadas por você e nunca ficam em arquivo. |
| 5 | Clicar em **Run workflow** nas pipelines | Execução manual exigida pelo PM-04. |
| 6 | *(Recomendado)* Criar um **alerta de orçamento** na AWS | Evita surpresa na fatura. |
| 7 | Rodar a pipeline **9 · Desativar** depois da apresentação | Para de gerar custo. |

Todo o resto é automático: a rede, as VMs, o Docker, o MongoDB, os contêineres, os backups, os testes e as evidências.

---

## 1. Conta AWS e usuário IAM (cerca de 10 min)

1. Acesse <https://aws.amazon.com/> e clique em **Create an AWS Account**. Siga o cadastro (e-mail, cartão e verificação por telefone).
   Escolha o plano **Free** ou **Paid**. Os dois funcionam, e o Free usa os créditos iniciais.
2. Entre no console, pesquise **IAM** e vá em **Users → Create user**.
   - Nome: `kubeshop-pipeline`. Deixe **sem** acesso ao console.
   - **Attach policies directly → `AdministratorAccess`**.
     > Para o laboratório isso simplifica bastante. Em produção, use OIDC com um papel restrito. Veja [01-arquitetura.md](01-arquitetura.md#credenciais-da-pipeline).
3. Abra o usuário e vá em **Security credentials → Create access key → "Application running outside AWS"**.
   Copie o **Access key ID** e o **Secret access key**. Mantenha a tela aberta até o passo 2.
4. *(Recomendado)* Em **Billing → Budgets → Create budget → Monthly cost budget**, defina US$ 20 com alerta por e-mail.

## 2. Ferramentas locais e GitHub (cerca de 5 min)

No **PowerShell**, dentro da pasta do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\install-tools.ps1
```

Isso instala Git, GitHub CLI e Terraform. Feche e abra o terminal se ele pedir. Depois rode:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\setup-github.ps1
```

O script faz o seguinte:
- abre o navegador para você autorizar o GitHub;
- cria o repositório `kubeshop-infra` (público, para o professor acessar o link) e envia o código;
- gera a chave SSH em `%USERPROFILE%\.ssh\kubeshop` e duas senhas aleatórias do MongoDB;
- pede o Access key ID e o Secret (que fica oculto ao digitar);
- grava tudo como **GitHub Secrets**. Nenhum valor é exibido nem salvo em arquivo do projeto.

Para usar um repositório privado: `setup-github.ps1 -Visibility private`. Nesse caso, adicione o professor como colaborador.

## 3. Criar o ambiente: Cenário 1 (cerca de 20 min)

No GitHub, vá em **Actions → "2 · Infra - Provisionar / Atualizar" → Run workflow**:

| Campo | Valor |
|---|---|
| environment | `dev` |
| run_mode | `apply` |
| instance_name | `kubeshop` |
| instance_type | `t3.micro` |
| db_instance_type | `t3.small` |
| db_volume_gb | `10` |
| docker_image | *(vazio)* |
| docker_tag | `1.0.0` |
| update_os | ✅ (na primeira execução) |
| extra_packages | `htop` |

O que acontece:
1. **Verificar imagens**: as imagens `1.0.0` ainda não existem. A pipeline chama o **CI/CD da aplicação**, que testa e constrói o KubeShop original e publica no GHCR.
2. **Terraform**: cria o bucket de state, o bucket de backups, a VPC, as duas VMs, os Security Groups, o EBS e o IAM.
3. **Ansible**: configura o NAT, atualiza o SO, instala pacotes, aplica o hardening de SSH, instala o Docker, prepara o volume, sobe o MongoDB, liga o backup diário e sobe a API e o frontend.
4. **Testes**: smoke pela internet e isolamento do banco.

Ao terminar, o **resumo da execução** mostra `Loja disponível em: http://X.X.X.X`. Abra no navegador.

**Teste a loja (ACE-04):** adicione um produto à sacola, confirme o pedido, recarregue a página (F5) e confira em **Meus pedidos**.

## 4. Atualizar o ambiente: Cenário 2

Rode a pipeline 2 de novo, mudando:

| Campo | De | Para | Ferramenta | Efeito |
|---|---|---|---|---|
| instance_type | `t3.micro` | `t3.small` | **Terraform** | VM da aplicação redimensionada in-place (`~ update`, sem recriar) |
| docker_tag | `1.0.0` | `1.1.0` | **Ansible** | imagem nova construída e contêineres recriados de forma controlada |
| extra_packages | `htop` | `htop, tree` | **Ansible** | pacote novo instalado |
| update_os | ✅ | ☐ | — | — |

No plan aparece `Plan: 0 to add, 1 to change, 0 to destroy`. O PLAY RECAP mostra `changed>0` só no que mudou.
Depois confira que **o pedido continua lá** (ACE-05: alteração de infraestrutura que preserva os dados).
Em `/api/info` aparece `"version":"1.1.0"`.

> Outras alterações de infraestrutura possíveis: `db_instance_type` t3.small → t3.medium (a VM do banco reinicia e os dados ficam no EBS) ou `db_volume_gb` 10 → 12 (disco ampliado online).

## 5. Reexecutar sem alterações: Cenário 3

Rode a pipeline 2 **com exatamente os mesmos parâmetros** do cenário 2. O esperado:
- Terraform: **"No changes. Your infrastructure matches the configuration."**
- Ansible: `changed=0` em todos os hosts. O resumo mostra **Idempotente**.

## 6. Operação e recuperação (ACE-07)

Vá em **Actions → "3 · Operação"** e rode, nesta ordem:
1. `action=backup`: o resultado mostra `BACKUP_OK key=dev/kubeshop-dev-…archive.gz orders=N`.
2. Crie mais um pedido na loja, que passa a ter N+1.
3. `action=list-backups`: tabela com a chave, a quantidade de pedidos e o SHA-256.
4. `action=restore`, `backup_key=latest`, `confirm=RESTAURAR`: o resultado mostra `RESTORE_OK … pedidos_backup=N pedidos_depois=N`. A loja volta a ter N pedidos.
5. `action=restart`: reinicia o banco, a API e o frontend. Os pedidos continuam (ACE-05).
6. `action=health` e `action=logs`: diagnóstico.

## 7. Desativar (depois da apresentação)

Vá em **Actions → "9 · Infra - Desativar"**, com `environment=dev` e `confirmation=DESTRUIR-dev`.
Um backup final vai para o S3 e todos os recursos do ambiente são removidos. Continuam existindo só os buckets de backup e de state, que custam centavos.

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `Credenciais AWS ausentes` | Secrets não configurados | rodar `setup-github.ps1` de novo |
| `InvalidClientTokenId` / `AuthFailure` | access key errada ou desativada | criar outra key no IAM e rodar o setup de novo |
| `VcpuLimitExceeded` / `Unsupported` no apply | limite de conta nova ou tipo indisponível | usar `t3.micro` nas duas VMs ou pedir aumento de cota |
| Ansible `UNREACHABLE` | VM ainda iniciando | rodar a pipeline de novo (é idempotente) |
| `denied` ao baixar a imagem | imagem de outro dono | deixar `docker_image` vazio |
| Loja abre mas mostra "indisponível" | API sem banco | rodar `3 · Operação` → `health` e depois `logs` (`service=api`) |

Mais detalhes em [03-manual-operacao.md](03-manual-operacao.md).
