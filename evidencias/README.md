# Evidências

Guarde aqui os prints e os artefatos das execuções usadas na apresentação e no PDF de entrega.
**Antes de salvar, confira que nenhum print mostra valores de secrets.** A tela de Secrets do GitHub só mostra os nomes, então pode aparecer.

| Arquivo sugerido | O que capturar | Critério |
|---|---|---|
| `01-cenario1-summary.png` | resumo do pipeline 2 (parâmetros, plan "X to add", PLAY RECAP, testes, URL) | Cenário 1, ACE-01 |
| `02-inventario-ec2.png` | console EC2 com as duas VMs (`kubeshop-dev-app`, `kubeshop-dev-db` sem IP público) | ACE-02 |
| `03-loja-pedido.png` | loja aberta, pedido confirmado, *Meus pedidos* depois de F5 | ACE-04 |
| `04-isolamento.png` | bloco "Testes" com `ISOLATION_RESULT=PASS` e "Mongo sem senha: RECUSADO" | ACE-03 |
| `05-cenario2-plan.png` | plan `0 to add, 1 to change, 0 to destroy` (`instance_type`) | Cenário 2 |
| `06-cenario2-recap.png` | PLAY RECAP com `changed>0` (nova tag/pacote) e `/api/info` com a nova versão | Cenário 2 |
| `07-persistencia.png` | *Meus pedidos* com o mesmo pedido depois do Cenário 2 e de `restart` | ACE-05 |
| `08-cenario3.png` | "No changes" no Terraform + "Idempotente: changed=0" | Cenário 3 |
| `09-backup-restore.png` | `BACKUP_OK` e `RESTORE_OK ... pedidos_backup=N pedidos_depois=N` | ACE-07 |
| `10-actions-historico.png` | lista de execuções dos pipelines (IDs das execuções) | ACE-08 |
| `11-secrets.png` | Settings → Secrets (só os nomes) | REQ-04 |
| `12-destroy.png` | resumo do pipeline 9 | desativação |

Os **artefatos** de cada execução (aba *Summary* → *Artifacts*) trazem `plan.txt`, `apply.txt`, `tf-outputs.json`,
`ansible.log`, `recap.txt`, `smoke.txt`, `isolation.txt` e `ops.log`. Baixe e salve aqui os das execuções citadas no relatório.
