# 05 · Procedimento administrativo de acesso ao banco (REQ-03)

O MongoDB **não é acessível pela internet**. A VM do banco não tem IP público, e o Security Group aceita as portas 27017 e 22
**somente** a partir da VM da aplicação. O acesso administrativo é sempre feito **por salto (ProxyJump)** via VM da aplicação.

> Use este procedimento só para diagnóstico excepcional. Rotinas comuns (saúde, logs, backup, restauração) estão no pipeline **3 · Operação** e não exigem acesso manual.

## 1. Liberar temporariamente o SSH para o seu IP

A porta 22 da VM da aplicação fica **fechada** por padrão. Escolha uma opção:

- **Temporária (recomendada):** no console AWS, vá em **EC2 → Security Groups → `kubeshop-dev-sg-app` → Edit inbound rules → Add rule**,
  com SSH e origem **My IP**. A descrição deve começar por `pipeline-runner-temporario`, para que a próxima execução da pipeline remova a regra automaticamente.
- **Permanente para a equipe:** defina a variável do repositório `ADMIN_CIDRS` como `["<seu-ip>/32"]` e rode o pipeline 2 (fica versionado no state).

## 2. Conectar

A chave privada está em `%USERPROFILE%\.ssh\kubeshop` (gerada pelo `setup-github.ps1`). Os IPs aparecem no resumo do pipeline 2.

```powershell
# VM da aplicação
ssh -i $HOME\.ssh\kubeshop ubuntu@<APP_PUBLIC_IP>

# VM do banco (salto pela VM da aplicação)
ssh -i $HOME\.ssh\kubeshop -o ProxyCommand="ssh -i $HOME\.ssh\kubeshop -W %h:%p ubuntu@<APP_PUBLIC_IP>" ubuntu@10.20.2.10
```

## 3. Consultar o MongoDB (na VM do banco)

```bash
# Quantidade de pedidos (a senha é lida do arquivo, não aparece no histórico)
sudo docker exec mongodb mongosh --quiet --file /opt/count-orders.js

# Shell administrativo interativo
sudo docker exec -it mongodb sh -c 'mongosh -u admin -p "$(cat /run/secrets/mongo_root_password)" --authenticationDatabase admin kubeshop'
# > db.orders.find().sort({createdAt:-1}).limit(5)
```

Comandos úteis: `sudo docker ps`, `sudo docker logs --tail 100 mongodb`, `df -h /data/mongo`,
`systemctl list-timers kubeshop-backup.timer` e `sudo /usr/local/bin/kubeshop-backup`.

## 4. Encerrar

Remova a regra de SSH criada no passo 1, ou rode qualquer pipeline (o fechamento automático remove regras com a descrição `pipeline-runner-temporario*`).
Não altere configurações manualmente nas VMs: a próxima execução do Ansible as restaura.

<a id="rotação-de-senhas"></a>
## Rotação de senhas do banco

A imagem oficial só cria os usuários na primeira inicialização. Para trocar uma senha:

1. Faça um backup (pipeline 3 → `backup`).
2. Conecte na VM do banco (passos 1 e 2) e altere no MongoDB:
   ```bash
   sudo docker exec -it mongodb sh -c 'mongosh -u admin -p "$(cat /run/secrets/mongo_root_password)" --authenticationDatabase admin'
   # > db.getSiblingDB("kubeshop").changeUserPassword("kubeshop", "<NOVA_SENHA_APP>")
   # > db.getSiblingDB("admin").changeUserPassword("admin", "<NOVA_SENHA_ROOT>")
   ```
3. Atualize os secrets `MONGO_APP_PASSWORD` e/ou `MONGO_ROOT_PASSWORD` no GitHub (**Settings → Secrets and variables → Actions**).
4. Rode o pipeline 2 com os mesmos parâmetros. O Ansible regrava os arquivos de senha e reinicia o banco e a API.

## Troca da chave SSH

1. Gere uma nova chave e adicione a **pública** em `~/.ssh/authorized_keys` das duas VMs (com a chave antiga ainda válida).
2. Atualize o secret `SSH_PRIVATE_KEY` e rode o pipeline 2. O `aws_key_pair` é atualizado e as VMs não são recriadas.
3. Remova a chave antiga do `authorized_keys`.
