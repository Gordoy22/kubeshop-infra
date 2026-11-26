# -*- coding: utf-8 -*-
"""Gera o roteiro da apresentação do PM-04 em PDF.

Uso:  python scripts/gerar-roteiro-pdf.py
Saída: entrega/PM04-KubeShop-Roteiro-Apresentacao.pdf
Reaproveita o estilo e os dados (integrantes, links, execuções) de gerar-relatorio-pdf.py.
"""
import importlib.util
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, PageBreak, SimpleDocTemplate, Spacer, Table, TableStyle

spec = importlib.util.spec_from_file_location("rel", Path(__file__).with_name("gerar-relatorio-pdf.py"))
rel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rel)
p, table, bullets, code, link, run, esc = rel.p, rel.table, rel.bullets, rel.code, rel.link, rel.run, rel.esc
H1, H2, BODY, SMALL, CELL = rel.H1, rel.H2, rel.BODY, rel.SMALL, rel.CELL
REPO, LOJA, INTEGRANTES = rel.REPO, rel.LOJA, rel.INTEGRANTES
A, B = (INTEGRANTES + ["Integrante 2"])[:2]
ACTIONS = f"{REPO}/actions"
OUT = rel.ROOT / "entrega" / "PM04-KubeShop-Roteiro-Apresentacao.pdf"


def bloco(num, titulo, tempo, quem, fala, mostrar, esperado=None):
    """Um bloco do roteiro: o que falar, onde clicar e o que deve aparecer."""
    head = Table([[p(f"<b>{num} · {esc(titulo)}</b>", rel.ParagraphStyle("bh", parent=CELL, fontSize=10.5,
                                                                          textColor=rel.colors.white)),
                   p(f"<b>{tempo}</b> · {esc(quem)}", rel.ParagraphStyle("bq", parent=CELL, alignment=2,
                                                                         textColor=rel.colors.white))]],
                 colWidths=[11.5 * cm, 5.5 * cm])
    head.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), rel.AZUL),
                              ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                              ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7)]))
    rows = [[p("<b>Fala</b>", CELL), [p(f, CELL) for f in fala]],
            [p("<b>Mostrar</b>", CELL), [p(m, CELL) for m in mostrar]]]
    if esperado:
        rows.append([p("<b>Deve aparecer</b>", CELL), [p(e, CELL) for e in esperado]])
    body = Table(rows, colWidths=[2.6 * cm, 14.4 * cm])
    body.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, rel.BORDA), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                              ("BACKGROUND", (0, 0), (0, -1), rel.FUNDO),
                              ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return [KeepTogether([head, body]), Spacer(1, 9)]


def build():
    s = []
    # ------------------------------------------------------------------ capa
    s += [Spacer(1, 2.6 * cm),
          p("PM-04 · PROJETO FINAL", rel.ParagraphStyle("k", parent=SMALL, fontSize=10, textColor=rel.LARANJA)),
          p("Roteiro da apresentação", rel.ParagraphStyle("t", parent=H1, fontSize=28, leading=34)),
          p("KubeShop na AWS com Terraform, Ansible e GitHub Actions",
            rel.ParagraphStyle("st", parent=BODY, fontSize=13, leading=17, textColor=rel.CINZA)),
          Spacer(1, 1 * cm)]
    t = Table([[p(f"<b>{a}</b>", CELL), p(b, CELL)] for a, b in [
        ("Apresentadores", f"{esc(A)} e {esc(B)}"),
        ("Duração sugerida", "15 a 18 minutos + perguntas"),
        ("Repositório", link(REPO)),
        ("Pipelines (Actions)", link(ACTIONS)),
        ("Loja", link(LOJA)),
        ("Documento de entrega", "entrega/PM04-KubeShop-Entrega.pdf"),
    ]], colWidths=[4.2 * cm, 12.8 * cm])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, rel.BORDA), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    s += [t, Spacer(1, 1 * cm)]
    s.append(p("<b>Ideia central da apresentação:</b> mostrar que a infraestrutura foi <b>projetada a partir da demanda</b> "
               "da Zibiska Korp (duas VMs, banco isolado, persistência, backup) e que <b>tudo é operado pela pipeline</b>: "
               "criação, atualização, reexecução sem alterações, backup, restauração e desativação, sem nenhum ajuste manual "
               "nos servidores."))
    s.append(p("<b>Estratégia:</b> logo no início, dispare uma execução ao vivo (Cenário 3). Ela roda em segundo plano enquanto "
               "vocês explicam a demanda e a arquitetura, e o resultado já está pronto quando chegarem na parte de evidências."))
    s.append(PageBreak())

    # ------------------------------------------------------------------ preparação
    s.append(p("1. Preparação", H1))
    s.append(p("Na véspera", H2))
    s.append(table([
        ["Item", "Como conferir"],
        ["Loja no ar", f"Abrir {link(LOJA)}: catálogo e o pedido #1ed462 em <i>Meus pedidos</i>."],
        ["Ambiente saudável", "Actions → <b>3 · Operação</b> → action=<b>health</b>. Esperado: verde, \"Mongo sem senha: RECUSADO\"."],
        ["Backup automático rodou", "Actions → <b>3 · Operação</b> → action=<b>logs</b>, service=<b>backup</b>. Esperado: execução diária às 03:00 UTC com <i>BACKUP_OK</i>."],
        ["Créditos AWS", "Console AWS → Billing: créditos restantes (ambiente custa ~US$ 1,25/dia)."],
        ["Ensaio", "Rodar o roteiro inteiro uma vez, cronometrando. Combinar quem fala cada bloco."],
    ], [4.2 * cm, 12.8 * cm]))
    s.append(p("30 minutos antes: abas abertas no navegador (nesta ordem)", H2))
    s.append(table([
        ["#", "Aba", "Endereço"],
        ["1", "PDF de entrega (diagrama e tabelas)", "entrega/PM04-KubeShop-Entrega.pdf"],
        ["2", "Repositório (estrutura de pastas)", link(REPO)],
        ["3", "Actions (histórico de execuções)", link(ACTIONS)],
        ["4", "Execução do Cenário 1", run("c1")],
        ["5", "Execução do Cenário 2", run("c2")],
        ["6", "Execução da restauração", run("restore")],
        ["7", "Console AWS → EC2 → Instâncias, região <b>Leste dos EUA (Ohio)</b>", "https://console.aws.amazon.com/ec2"],
        ["8", "Console AWS → EC2 → Security Groups (kubeshop-dev-sg-db)", "mesmo console"],
        ["9", "Loja", link(LOJA)],
    ], [0.8 * cm, 8.4 * cm, 7.8 * cm]))
    s.append(Spacer(1, 6))
    s += bullets([
        "Estar <b>logado no GitHub</b> (conta Gordoy22) e no <b>console da AWS</b>. Sem login o GitHub não mostra os resumos detalhados.",
        "Aumentar o zoom do navegador (Ctrl + +) para o projetor.",
        "Nunca abrir a tela de valores de secrets nem o arquivo da chave SSH durante a apresentação.",
    ])

    # ------------------------------------------------------------------ cronograma
    s.append(PageBreak())
    s.append(p("2. Divisão do tempo", H1))
    s.append(table([
        ["Bloco", "Tempo", "Quem", "Conteúdo"],
        ["0", "0:30", A, "Disparar o Cenário 3 ao vivo (fica rodando)"],
        ["1", "2:00", A, "Demanda da Zibiska Korp e requisitos"],
        ["2", "3:00", B, "Arquitetura e decisões técnicas"],
        ["3", "2:00", B, "Organização do código (Terraform, Ansible, pipelines)"],
        ["4", "3:00", A, "Cenário 1: criação do zero (evidência) + VMs no console"],
        ["5", "1:30", A, "Aplicação funcionando ao vivo"],
        ["6", "2:00", B, "Cenário 2 (evidência) e Cenário 3 (resultado ao vivo)"],
        ["7", "2:00", B, "Operação: backup, restauração e isolamento do banco"],
        ["8", "1:30", A, "Segurança dos segredos e custos"],
        ["9", "0:30", "Ambos", "Encerramento e perguntas"],
    ], [1.3 * cm, 1.6 * cm, 4.1 * cm, 10.0 * cm]))
    s.append(p("A divisão é uma sugestão; troquem os blocos como preferirem, mas ambos precisam falar (regra do PM-04).", SMALL))

    # ------------------------------------------------------------------ blocos
    s.append(p("3. Roteiro passo a passo", H1))
    s += bloco(0, "Disparar a execução ao vivo", "0:30", A,
               ["\"Antes de começar, vou disparar a pipeline com os mesmos parâmetros da última execução. "
                "Ela vai rodar enquanto explicamos, e no fim vamos ver o resultado.\""],
               ["Aba 3 (Actions) → <b>2 · Infra - Provisionar / Atualizar</b> → <b>Run workflow</b>.",
                "Preencher: environment <b>dev</b> · run_mode <b>apply</b> · instance_name <b>kubeshop</b> · instance_type <b>t3.small</b> · "
                "db_instance_type <b>t3.small</b> · db_volume_gb <b>10</b> · docker_image <i>(vazio)</i> · docker_tag <b>1.1.0</b> · "
                "update_os <b>desmarcado</b> · extra_packages <b>htop, tree</b> → <b>Run workflow</b>."],
               ["A execução aparece no topo da lista, em andamento (leva cerca de 4 minutos)."])
    s += bloco(1, "A demanda", "2:00", A,
               ["\"A Zibiska Korp é uma holding de varejo que quer lançar o KubeShop, seu marketplace. O código já existe; "
                "ela precisava de alguém para colocá-lo na nuvem e automatizar a administração da infraestrutura.\"",
                "\"Os requisitos principais: no mínimo duas VMs, com o MongoDB numa VM exclusiva; o banco sem porta pública, "
                "acessível só pela aplicação pela rede privada; credenciais fora do código e dos logs; pedidos preservados "
                "após reinícios e alterações; backup, restauração e desativação documentados.\"",
                "\"Não alteramos a aplicação: usamos o código original do repositório do professor, inclusive os Dockerfiles.\""],
               ["PDF de entrega, seção 2 (tabela de requisitos REQ-01 a REQ-05)."])
    s += bloco(2, "Arquitetura e decisões", "3:00", B,
               ["\"Escolhemos a AWS. São duas VMs Ubuntu 24.04: a da aplicação, numa sub-rede pública com IP fixo, roda o "
                "frontend em Nginx e a API Node em contêineres Docker. A do banco fica numa sub-rede privada, <b>sem IP público</b>, "
                "e o firewall só aceita a porta do MongoDB vinda da VM da aplicação.\"",
                "\"Os dados do MongoDB ficam num disco EBS separado: dá para trocar o tamanho da VM ou até recriá-la "
                "sem perder os pedidos.\"",
                "\"Uma curiosidade: começamos na us-east-1, mas a conta está no plano Free da AWS, que só libera a us-east-2. "
                "Criamos um pipeline de diagnóstico que testou cada permissão e provou isso, e mudamos a região, que é um parâmetro.\"",
                "\"Para economizar, a própria VM da aplicação faz o NAT do banco, em vez de um NAT Gateway de US$ 33 por mês. "
                "O state do Terraform fica num bucket S3 versionado, criptografado e com lock.\""],
               ["PDF de entrega, seção 3 (Figura 1 e tabela de decisões)."])
    s += bloco(3, "Organização do código", "2:00", B,
               ["\"O Terraform está separado em duas partes: <i>global</i>, com o bucket de backups que sobrevive à desativação, "
                "e <i>environment</i>, com rede, VMs, firewall, disco e IAM, um state por ambiente.\"",
                "\"O Ansible tem uma role por responsabilidade: atualização do SO, pacotes, segurança do SSH, NAT, Docker, "
                "volume de dados, MongoDB, backup, contêineres e verificação.\"",
                "\"São cinco pipelines principais: CI, CI/CD da aplicação, provisionar/atualizar, operação e desativação.\""],
               ["Aba 2 (repositório): pastas <b>terraform/</b>, <b>ansible/roles/</b> e <b>.github/workflows/</b>.",
                "Opcional: abrir <b>ansible/roles/containers/tasks/main.yml</b> para mostrar a tag vinda do parâmetro."])
    s += bloco(4, "Cenário 1: criação do zero", "3:00", A,
               ["\"No Cenário 1 rodamos a pipeline com o ambiente vazio. Ela primeiro construiu as imagens da aplicação, "
                "depois o Terraform criou 32 recursos, e o Ansible preparou as duas VMs do zero.\"",
                "\"Os parâmetros entram como variáveis do Terraform e extra-vars do Ansible. Os IPs que o Terraform cria "
                "viram o inventário do Ansible automaticamente.\""],
               ["Aba 4 (run do Cenário 1): resumo com os parâmetros, <i>Plan: 32 to add</i>, PLAY RECAP e testes.",
                "Aba 7 (EC2): as duas instâncias. Clicar em <b>kubeshop-dev-db</b> e mostrar que <b>IPv4 público</b> está vazio."],
               ["Ansible com <i>failed=0</i>; testes <i>SMOKE_RESULT=PASS</i> e <i>ISOLATION_RESULT=PASS</i>."])
    s += bloco(5, "Aplicação ao vivo", "1:30", A,
               ["\"Esta é a loja original, rodando na VM da aplicação e gravando no MongoDB da outra VM.\""],
               ["Aba 9 (loja): adicionar um produto à sacola → <b>Confirmar pedido fictício</b>.",
                "Apertar <b>F5</b> → aba <b>Meus pedidos</b>: o pedido novo e o #1ed462, criado dias antes."],
               ["Confirmação do pedido e histórico mantido após recarregar."])
    s += bloco(6, "Cenários 2 e 3", "2:00", B,
               ["\"No Cenário 2 mudamos parâmetros: o Terraform aumentou a VM da aplicação de t3.micro para t3.small "
                "<b>sem recriar</b>, e o Ansible instalou um pacote novo e atualizou a aplicação de 1.0.0 para 1.1.0. "
                "O pedido continuou lá.\"",
                "\"E agora o resultado da execução que disparamos no começo, o Cenário 3: mesmos parâmetros, nada para mudar.\""],
               ["Aba 5 (run do Cenário 2): <i>~ instance_type = \"t3.micro\" -> \"t3.small\"</i> e <i>Plan: 0 to add, 1 to change</i>.",
                "Aba 3 (Actions): abrir a execução disparada no bloco 0."],
               ["Terraform: <b>No changes. Your infrastructure matches the configuration.</b>",
                "Ansible: <b>changed=0</b> nos dois hosts (resumo mostra \"Idempotente\")."])
    s += bloco(7, "Operação, backup e restauração", "2:00", B,
               ["\"O backup roda todo dia às 03:00 UTC na VM do banco e vai para o S3. Para provar a restauração, fizemos um "
                "backup com 1 pedido, criamos um pedido extra e restauramos: voltou a ter exatamente 1, com o SHA-256 conferido.\"",
                "\"O banco também é testado contra acesso sem senha: a conexão é recusada.\""],
               ["Aba 6 (run da restauração): linha <i>RESTORE_OK … pedidos_antes=2 pedidos_backup=1 pedidos_depois=1</i>.",
                "Aba 8 (Security Group do banco): regras de entrada com origem no SG da aplicação, nenhuma por IP."],
               ["Regras 27017 e 22 com origem <i>sg-…</i> (da aplicação)."])
    s += bloco(8, "Segurança e custos", "1:30", A,
               ["\"Nenhuma senha está no código: chaves da AWS, chave SSH e senhas do banco ficam nos GitHub Secrets, "
                "foram geradas por script e nunca exibidas. O CI roda o gitleaks a cada push. A porta SSH fica fechada e "
                "só abre para o IP da própria pipeline durante a execução.\"",
                "\"O custo estimado é de cerca de US$ 30 a 38 por mês por ambiente, e hoje sai dos créditos do plano Free. "
                "Depois da apresentação, a pipeline de desativação faz um backup final e remove tudo.\""],
               ["Repositório → Settings → Secrets and variables → Actions (só os <b>nomes</b> aparecem).",
                "PDF de entrega, seção 6 (tabela de custos)."])
    s += bloco(9, "Encerramento", "0:30", "Ambos",
               ["\"Resumindo: a infraestrutura foi desenhada a partir da demanda, é reproduzível, atualizável e idempotente, "
                "e toda a operação acontece pelas pipelines. Obrigado, estamos abertos a perguntas.\""],
               ["Aba 3 (Actions): histórico com todas as execuções."])

    # ------------------------------------------------------------------ plano B
    s.append(p("4. Plano B (se algo der errado ao vivo)", H1))
    s.append(table([
        ["Situação", "O que fazer"],
        ["Execução ao vivo demorando", "Seguir a apresentação e mostrar o Cenário 3 já registrado: " + run("c3") + "."],
        ["Execução ao vivo falhou", "Abrir o job vermelho e ler o erro em voz alta (mostra que a pipeline para no erro e o log é claro). "
                                     "Depois mostrar o Cenário 3 registrado. Causas comuns: VM reiniciando (rodar de novo) ou crédito/credencial AWS."],
        ["Loja fora do ar", "3 · Operação → <b>health</b>; se acusar problema, <b>restart</b> com service=all (cerca de 1 minuto)."],
        ["Sem internet / projetor", "Apresentar pelo PDF de entrega: todas as evidências e números das execuções estão nele."],
        ["Login do GitHub ou AWS expirou", "Entrar de novo antes do bloco; o histórico de execuções é público mesmo sem login."],
    ], [4.6 * cm, 12.4 * cm]))

    # ------------------------------------------------------------------ perguntas
    s.append(p("5. Perguntas prováveis", H1))
    faq = [
        ("Por que AWS e por que us-east-2?",
         "AWS foi a nuvem das aulas de Terraform e tem créditos no plano Free. A região us-east-2 tem o mesmo preço da us-east-1 "
         "e é a única liberada pela política do plano Free desta conta, o que comprovamos com o pipeline 8 · Diagnóstico."),
        ("Como o banco fica isolado?",
         "Quatro camadas: sem IP público e em sub-rede privada; Security Group que só aceita o SG da aplicação; porta 27017 "
         "publicada só no IP privado; e autenticação obrigatória (acesso sem senha é recusado, testado a cada execução)."),
        ("Como a VM do banco instala pacotes sem internet?",
         "A VM da aplicação faz NAT só de saída para a sub-rede privada. Ninguém da internet consegue iniciar conexão com o banco."),
        ("Onde fica o state do Terraform e o que acontece se dois rodarem juntos?",
         "Num bucket S3 versionado e criptografado, um state por ambiente. O lock do S3 e a concorrência da pipeline por ambiente "
         "impedem execuções simultâneas; versões antigas permitem recuperar o state."),
        ("Como vocês garantem que não recria a VM sem necessidade?",
         "Mudanças de tipo de VM são in-place, a AMI é ignorada após a criação e os dados ficam num disco separado. "
         "O Cenário 3 mostra \"No changes\"."),
        ("O que é idempotência no Ansible e como provaram?",
         "Rodar de novo com os mesmos parâmetros leva ao mesmo estado sem alterar nada: usamos módulos declarativos em vez de "
         "comandos soltos. O Cenário 3 terminou com changed=0 nos dois hosts."),
        ("Onde estão as senhas?",
         "Só nos GitHub Secrets. O GitHub mascara nos logs, as tarefas do Ansible com senha usam no_log, e nas VMs as senhas "
         "ficam em arquivos 0400 montados nos contêineres. O state do Terraform não tem senhas."),
        ("Como atualizar ou voltar a versão da aplicação?",
         "Trocando o parâmetro docker_tag: o Ansible baixa a imagem e recria só os contêineres. Para voltar, roda com a tag anterior."),
        ("E se a VM do banco for perdida?",
         "A pipeline recria a VM e reanexa o mesmo disco EBS. Se o disco também for perdido, recria e restaura o último backup do S3."),
        ("Quanto custa e o que continua cobrando depois de desativar?",
         "Cerca de US$ 30 a 38 por mês por ambiente. Depois da desativação ficam só os buckets de backup e de state (centavos por mês)."),
        ("Por que não tem HTTPS?",
         "Não há domínio, e certificado público exige um. A loja é fictícia, sem login nem pagamento. Em produção: domínio no Route 53 "
         "e certificado Let's Encrypt, ou um Load Balancer com certificado gratuito da AWS."),
        ("Quais as limitações?",
         "Uma instância de cada serviço (sem alta disponibilidade), backup diário (RPO de 24 horas), HTTP sem TLS e o NAT na VM da aplicação."),
    ]
    s.append(table([["Pergunta", "Resposta curta"]] + [[f"<b>{esc(q)}</b>", esc(r)] for q, r in faq],
                   [5.0 * cm, 12.0 * cm]))

    # ------------------------------------------------------------------ depois
    s.append(p("6. Depois da apresentação", H1))
    s += bullets([
        "Actions → <b>9 · Infra - Desativar ambiente (DESTRUTIVO)</b> → environment <b>dev</b>, confirmation <b>DESTRUIR-dev</b>, "
        "final_backup marcado, remove_backup_bucket desmarcado → Run workflow.",
        "Conferir no resumo o <i>BACKUP_OK</i> final e <i>Destroy complete</i>. Para recriar no futuro: pipeline 2 e depois "
        "3 · Operação → restore (latest, RESTAURAR).",
    ])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                            bottomMargin=1.8 * cm, title="PM-04 · Roteiro da apresentação",
                            author=", ".join(INTEGRANTES), subject="Roteiro da apresentação do projeto KubeShop")
    doc.build(s, onFirstPage=rel.on_page, onLaterPages=rel.on_page)
    print(f"PDF gerado: {OUT}")


if __name__ == "__main__":
    build()
