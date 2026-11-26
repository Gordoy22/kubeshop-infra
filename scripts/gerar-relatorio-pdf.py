# -*- coding: utf-8 -*-
"""Gera o PDF de entrega do PM-04 (KubeShop) a partir das evidências versionadas.

Uso:  python scripts/gerar-relatorio-pdf.py
Saída: entrega/PM04-KubeShop-Entrega.pdf

Os trechos de evidência (plan, PLAY RECAP, smoke e isolamento) são lidos dos artefatos
baixados das execuções em evidencias/, sem digitação manual.
Para incluir mais integrantes, edite a lista INTEGRANTES abaixo e rode de novo.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle, XPreformatted)

# ----------------------------------------------------------------------------- dados
INTEGRANTES = ["Joao Victor Godoy", "Mohammed Jebai"]
REPO = "https://github.com/Gordoy22/kubeshop-infra"
APP_REPO = "https://github.com/LaercioMLB/kube-shop-v2"
LOJA = "http://18.217.103.51"
DATA = "26/11/2026"
RUNS = {
    "img": "45869148123", "c1": "45870323873", "c2": "45874087005", "c3": "45874953922",
    "health": "45875471275", "restart": "45875661419", "backup": "45875935548",
    "smoke": "45876148765", "list": "45876254224", "restore": "45876364892",
    "diag": "45869784055",
}

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidencias"
IMG = EV / "img"
OUT = ROOT / "entrega" / "PM04-KubeShop-Entrega.pdf"

# ----------------------------------------------------------------------------- estilo
AZUL = colors.HexColor("#17406D")
LARANJA = colors.HexColor("#E8762B")
CINZA = colors.HexColor("#5B6573")
FUNDO = colors.HexColor("#F2F5F9")
VERDE = colors.HexColor("#1F7A3A")
BORDA = colors.HexColor("#C9D3DF")

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=17,
                    textColor=AZUL, spaceBefore=4, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12.5,
                    textColor=AZUL, spaceBefore=10, spaceAfter=5)
BODY = ParagraphStyle("B", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.6,
                      leading=13.4, spaceAfter=5)
SMALL = ParagraphStyle("S", parent=BODY, fontSize=8.2, leading=10.6, textColor=CINZA)
CELL = ParagraphStyle("C", parent=BODY, fontSize=8.4, leading=10.8, spaceAfter=0)
CELLB = ParagraphStyle("CB", parent=CELL, fontName="Helvetica-Bold")
HEAD = ParagraphStyle("HD", parent=CELL, fontName="Helvetica-Bold", textColor=colors.white)
CODE = ParagraphStyle("CODE", fontName="Courier", fontSize=7.3, leading=9.0, textColor=colors.HexColor("#E6EDF5"))
BUL = ParagraphStyle("BUL", parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=2)


def p(t, st=BODY):
    return Paragraph(t, st)


def esc(t):
    return escape(t)


def link(url, txt=None):
    return f'<link href="{url}" color="#1F5FBF"><u>{esc(txt or url)}</u></link>'


def run(key, label=None):
    return link(f"{REPO}/actions/runs/{RUNS[key]}", label or f"run {RUNS[key]}")


def bullets(items):
    return [Paragraph(i, BUL, bulletText="•") for i in items]


def table(rows, widths, header=True, zebra=True):
    data = []
    for i, r in enumerate(rows):
        st = HEAD if (header and i == 0) else CELL
        data.append([c if not isinstance(c, str) else Paragraph(c, st) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), AZUL))
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), FUNDO))
    t.setStyle(TableStyle(style))
    return t


def code(text, title=None):
    text = re.sub(r"\x1b\[[0-9;]*m", "", text).rstrip()
    # PLAY RECAP: remove colunas sempre zeradas e espaços excedentes para caber na página
    text = re.sub(r"\s+rescued=0\s+ignored=0", "", text)
    text = re.sub(r"(?<=\S) {3,}(?=\S)", "  ", text) if "PLAY RECAP" in text else text
    # fonte se ajusta à linha mais longa (Courier: largura do caractere = 0,6 × tamanho)
    usable = 17 * cm - 14
    longest = max((len(ln) for ln in text.splitlines()), default=1)
    size = max(5.2, min(7.3, usable / (0.6 * longest)))
    style = ParagraphStyle("CODEfit", parent=CODE, fontSize=size, leading=size * 1.23)
    inner = [XPreformatted(esc(text), style)]
    t = Table([[inner]], colWidths=[17 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F1B2A")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    out = []
    if title:
        out.append(p(f"<b>{esc(title)}</b>", SMALL))
    out.append(t)
    out.append(Spacer(1, 6))
    return out


def image(path, width_cm, caption):
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    width = width_cm * cm
    height = width * h / w
    max_h = 21 * cm
    if height > max_h:
        width, height = width * max_h / height, max_h
    img = Image(str(path), width=width, height=height)
    img.hAlign = "CENTER"
    frame = Table([[img]], colWidths=[width + 4])
    frame.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, BORDA),
                               ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                               ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return [frame, p(caption, ParagraphStyle("cap", parent=SMALL, alignment=TA_CENTER)), Spacer(1, 6)]


def read(rel):
    f = EV / rel
    return f.read_text(encoding="utf-8", errors="replace") if f.exists() else f"(arquivo não encontrado: {rel})"


def find_dir(prefix):
    return next((d for d in EV.glob(prefix + "*") if d.is_dir()), None)


# ----------------------------------------------------------------------------- diagrama
def diagrama():
    d = Drawing(17 * cm, 8.6 * cm)
    W, H = 17 * cm, 8.6 * cm

    def box(x, y, w, h, fill, stroke, title, lines, tcolor=colors.black):
        d.add(Rect(x, y, w, h, rx=6, ry=6, fillColor=fill, strokeColor=stroke, strokeWidth=1))
        d.add(String(x + 7, y + h - 14, title, fontName="Helvetica-Bold", fontSize=8.6, fillColor=tcolor))
        for i, ln in enumerate(lines):
            d.add(String(x + 7, y + h - 27 - i * 10.5, ln, fontName="Helvetica", fontSize=7.4, fillColor=tcolor))

    def arrow(x1, y1, x2, y2, label="", color=AZUL):
        d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1.3))
        import math
        a = math.atan2(y2 - y1, x2 - x1)
        s = 6
        d.add(Polygon([x2, y2, x2 - s * math.cos(a - 0.4), y2 - s * math.sin(a - 0.4),
                       x2 - s * math.cos(a + 0.4), y2 - s * math.sin(a + 0.4)], fillColor=color, strokeColor=color))
        if label:
            d.add(String((x1 + x2) / 2 - len(label) * 1.8, (y1 + y2) / 2 + 4, label,
                         fontName="Helvetica", fontSize=6.8, fillColor=CINZA))

    # nuvem AWS / VPC
    d.add(Rect(118, 8, W - 126, H - 16, rx=8, ry=8, fillColor=colors.HexColor("#FBFCFE"),
               strokeColor=LARANJA, strokeWidth=1.2, strokeDashArray=[4, 2]))
    d.add(String(126, H - 22, "AWS us-east-2 (Ohio)  ·  VPC kubeshop-dev-vpc 10.20.0.0/16",
                 fontName="Helvetica-Bold", fontSize=8, fillColor=LARANJA))
    # sub-redes
    d.add(Rect(128, 92, 190, 128, rx=6, ry=6, fillColor=colors.HexColor("#EEF5FF"), strokeColor=BORDA))
    d.add(String(134, 208, "Sub-rede pública 10.20.1.0/24", fontName="Helvetica", fontSize=7, fillColor=CINZA))
    d.add(Rect(330, 92, 140 + 18, 128, rx=6, ry=6, fillColor=colors.HexColor("#FFF4EC"), strokeColor=BORDA))
    d.add(String(336, 208, "Sub-rede privada 10.20.2.0/24", fontName="Helvetica", fontSize=7, fillColor=CINZA))

    box(10, 128, 92, 54, colors.white, BORDA, "Usuários", ["navegador", "HTTP :80"])
    box(136, 100, 174, 100, colors.white, AZUL, "VM 1 · kubeshop-dev-app",
        ["t3.small · Ubuntu 24.04 · 10.20.1.10", "Elastic IP 18.217.103.51",
         "Docker: frontend (Nginx + React) :80", "Docker: api (Node.js/Express)",
         "NAT da sub-rede privada", "SSH só p/ IP do runner (temporário)"])
    box(338, 100, 142, 100, colors.white, AZUL, "VM 2 · kubeshop-dev-db",
        ["t3.small · SEM IP público", "10.20.2.10", "Docker: mongo:8.0.17 autenticado",
         "27017 publicada só no IP privado", "SG: aceita só o SG da VM app"])
    box(338, 18, 142, 60, colors.white, BORDA, "EBS gp3 10 GiB (criptografado)",
        ["/data/mongo · dados persistentes", "sobrevive à troca/recriação da VM"])
    box(136, 18, 174, 60, colors.white, BORDA, "S3 kubeshop-backups-<conta>",
        ["mongodump diário 03:00 UTC + sob demanda", "versionado · SSE · retenção 30 dias",
         "acesso via VPC endpoint (rede AWS)"])

    arrow(102, 155, 136, 155, "")
    arrow(310, 150, 338, 150, "27017")
    arrow(409, 100, 409, 78, "")
    arrow(338, 120, 300, 78, "")
    d.add(String(10, 96, "GitHub Actions", fontName="Helvetica-Bold", fontSize=7.6, fillColor=AZUL))
    d.add(String(10, 86, "Terraform -> Ansible", fontName="Helvetica", fontSize=7, fillColor=CINZA))
    d.add(String(10, 76, "state: S3 versionado", fontName="Helvetica", fontSize=7, fillColor=CINZA))
    d.add(String(10, 66, "+ lock (use_lockfile)", fontName="Helvetica", fontSize=7, fillColor=CINZA))
    arrow(80, 100, 150, 112, "", color=LARANJA)
    return d


# ----------------------------------------------------------------------------- páginas
def on_page(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setStrokeColor(LARANJA)
        canvas.setLineWidth(2)
        canvas.line(2 * cm, A4[1] - 1.25 * cm, A4[0] - 2 * cm, A4[1] - 1.25 * cm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(CINZA)
        canvas.drawString(2 * cm, A4[1] - 1.05 * cm, "PM-04 · Projeto Final · KubeShop na AWS (Terraform + Ansible + GitHub Actions)")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
        canvas.drawString(2 * cm, 1.2 * cm, REPO)
    canvas.restoreState()


def build():
    story = []
    c1 = find_dir("cenario1-run")
    c2 = find_dir("cenario2-run")
    c3 = find_dir("cenario3-run")

    # ---------------- capa
    story += [Spacer(1, 3.2 * cm),
              p("PM-04 · PROJETO FINAL", ParagraphStyle("k", parent=SMALL, fontSize=10, textColor=LARANJA)),
              p("KubeShop na nuvem AWS", ParagraphStyle("t", parent=H1, fontSize=30, leading=36)),
              p("Automação de infraestrutura com Terraform, Ansible e GitHub Actions",
                ParagraphStyle("st", parent=BODY, fontSize=13, leading=17, textColor=CINZA)),
              Spacer(1, 1.2 * cm)]
    capa = [
        ["Integrantes", "<br/>".join(esc(n) for n in INTEGRANTES)],
        ["Repositório Git", link(REPO)],
        ["Loja publicada", link(LOJA) + " (ambiente <i>dev</i>, enquanto ativo)"],
        ["Cliente / demanda", "Zibiska Korp · Escopo KubeShop v1.2 (11/11/2026)"],
        ["Código da aplicação", link(APP_REPO, "LaercioMLB/kube-shop-v2") + " @ ee30950 (sem alterações)"],
        ["Provedor", "AWS · us-east-2 (Ohio)"],
        ["Data", DATA],
    ]
    t = Table([[p(f"<b>{a}</b>", CELL), p(b, CELL)] for a, b in capa], colWidths=[4.2 * cm, 12.8 * cm])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDA), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [t, Spacer(1, 1.4 * cm)]
    story += [p("<b>Resultado:</b> as duas VMs (aplicação e MongoDB exclusivo, este sem IP público) foram provisionadas "
                "pelo Terraform e configuradas pelo Ansible a partir da pipeline. Os três cenários obrigatórios "
                "(criação, atualização e reexecução sem alterações), o backup e a restauração verificada foram "
                "executados com sucesso e estão documentados com os números das execuções.", BODY)]
    story.append(PageBreak())

    # ---------------- 1. resumo
    story.append(p("1. Resumo da entrega", H1))
    story.append(table([
        ["Teste / critério", "Resultado", "Execução"],
        ["Cenário 1 · Criação inicial", "32 recursos criados; Ansible failed=0; loja, catálogo e isolamento OK", run("c1")],
        ["Cenário 2 · Atualização", "Terraform: VM app t3.micro -> t3.small in-place (0 add, 1 change, 0 destroy). "
                                    "Ansible: pacote tree + app 1.0.0 -> 1.1.0. Pedido preservado.", run("c2")],
        ["Cenário 3 · Reexecução", "Terraform <b>No changes</b>; Ansible <b>changed=0</b> nos 2 hosts", run("c3")],
        ["Reinício (ACE-05)", "banco -> API -> frontend reiniciados; pedido preservado", run("restart")],
        ["Backup (ACE-07)", "BACKUP_OK orders=1 enviado ao S3 (sha256 registrado)", run("backup")],
        ["Restauração (ACE-07)", "sha256=OK · pedidos_antes=2 · pedidos_backup=1 · pedidos_depois=1", run("restore")],
        ["CI do repositório", "fmt/validate Terraform, syntax-check + ansible-lint, actionlint, shellcheck, gitleaks", link(f"{REPO}/actions/workflows/ci.yml", "workflow 0 · CI")],
    ], [4.0 * cm, 9.6 * cm, 3.4 * cm]))
    story.append(Spacer(1, 8))
    story += bullets([
        "Aplicação <b>original e sem alterações visuais</b>: imagens construídas com os Dockerfiles do repositório do cliente.",
        "Toda mudança foi feita <b>pela pipeline</b> (workflow_dispatch com parâmetros), sem ajustes manuais nos servidores.",
        "Credenciais somente em <b>GitHub Secrets</b>; nenhum segredo no código, no state do Terraform ou nos logs.",
    ])

    # ---------------- 2. demanda
    story.append(p("2. Análise da demanda", H1))
    story.append(p("A Zibiska Korp quer publicar o KubeShop (marketplace fictício: catálogo, sacola e pedidos) na nuvem, com "
                   "aplicação e banco em servidores distintos e a administração da infraestrutura feita por pipelines. "
                   "A análise do repositório (compose.yaml, Dockerfiles, nginx.conf e configuração da API) identificou:"))
    story.append(table([
        ["Componente", "Tecnologia", "Necessidade de infraestrutura"],
        ["Frontend", "React (Vite) servido por Nginx :8080", "Entrada pública; encaminha /api para o host <b>api:3000</b>"],
        ["API", "Node.js 24 / Express", "Variáveis MONGO_HOST/USERNAME/PASSWORD_FILE; saúde em /api/health/ready"],
        ["Banco", "MongoDB 8.0.17 autenticado", "VM exclusiva, rede privada, persistência e backup"],
        ["CI/CD da aplicação", "considerado existente", "Pontos de integração documentados: imagens no GHCR + deploy por tag"],
    ], [3.0 * cm, 5.0 * cm, 9.0 * cm]))
    story.append(Spacer(1, 6))
    story.append(table([
        ["Requisito do escopo", "Como foi atendido"],
        ["REQ-01 · Duas VMs, MongoDB exclusivo", "aws_instance <b>app</b> e <b>db</b>; recursos extras justificados (EIP, EBS, S3, IAM, endpoint S3)"],
        ["REQ-02 · Banco isolado, sem porta pública", "VM do banco em sub-rede privada <b>sem IP público</b>; 27017 publicada só em 10.20.2.10"],
        ["REQ-03 · Acesso ao banco só pela VM app (rede privada)", "SG do banco aceita 27017/22 apenas do SG da aplicação; procedimento administrativo por ProxyJump documentado (docs/05)"],
        ["REQ-04 · Acessos restritos, credenciais fora do repo/logs", "SSH só por chave, sem root; porta 22 fechada (aberta só para o IP do runner durante a execução); Secrets + no_log + gitleaks"],
        ["REQ-05 · Persistência após reinício e alteração de infra", "Volume EBS dedicado; Docker só inicia após o volume montado; comprovado no Cenário 2 e no reinício"],
        ["§9 · Validar, provisionar, atualizar, manter, proteger, desativar", "Pipelines 0, 1, 2, 3 e 9 (seção 4)"],
    ], [5.6 * cm, 11.4 * cm]))

    # ---------------- 3. arquitetura
    story.append(PageBreak())
    story.append(p("3. Decisões de arquitetura", H1))
    story.append(diagrama())
    story.append(p("Figura 1 · Arquitetura implantada (ambiente dev).", ParagraphStyle("c", parent=SMALL, alignment=TA_CENTER)))
    story.append(Spacer(1, 6))
    story.append(table([
        ["Decisão", "Escolha", "Justificativa"],
        ["Provedor", "AWS", "Provider Terraform oficial e maduro; usado nas aulas; plano gratuito com créditos cobre o projeto."],
        ["Região", "us-east-2 (Ohio)", "Mesmo preço da us-east-1 (a mais barata). Obrigatória nesta conta: o plano Free aplica uma "
                                       "SCP de organização que só libera us-east-2 — comprovado pelo pipeline 8 · Diagnóstico ("
                                       + run("diag") + ")."],
        ["IaC", "Terraform 1.17 + hashicorp/aws ~> 6.0", "Declarativo, plano prévio, state remoto, atualização in-place."],
        ["Configuração", "Ansible (ansible-core 2.18, community.docker)", "Agentless (SSH), idempotente, roles por responsabilidade."],
        ["Pipelines", "GitHub Actions", "workflow_dispatch com parâmetros, Secrets, environments e artefatos de evidência."],
        ["Execução nas VMs", "Docker Engine", "Reaproveita imagens e hardening do compose validado (read-only, cap_drop, healthchecks)."],
        ["Sistema operacional", "Ubuntu Server 24.04 LTS", "Suporte até 2029, Python 3.12 nativo, repositório oficial Docker."],
        ["DNS / TLS", "não utilizados", "Sem domínio fornecido; loja fictícia sem login/pagamento. Caminho p/ produção: Route 53 + Let's Encrypt (Caddy) ou ALB + ACM."],
    ], [3.0 * cm, 4.2 * cm, 9.8 * cm]))
    story.append(p("Dimensionamento e recursos", H2))
    story.append(table([
        ["Recurso", "Configuração", "Motivo"],
        ["VM app", "t3.micro (Cenário 1) -> t3.small (Cenário 2)", "Nginx estático + API leve; tipo é parâmetro da pipeline"],
        ["VM db", "t3.small (2 vCPU, 2 GiB)", "MongoDB 8 com cache WiredTiger de 0,25 GB (igual ao original) + folga para mongodump"],
        ["Discos", "gp3 20 GiB (SO) ×2 + gp3 10 GiB (dados), criptografados", "gp3 é o mais barato com IOPS garantidas"],
        ["Rede", "VPC por ambiente (10.20/10.30/10.40), sub-rede pública e privada, EIP", "Isolamento e endereço fixo da loja"],
        ["NAT", "a própria VM app faz NAT da sub-rede privada", "Economiza ~US$ 33/mês do NAT Gateway (opção use_nat_gateway disponível)"],
        ["Backups", "S3 versionado, SSE, retenção 30 dias, endpoint S3 gateway", "Fora das VMs, sem tráfego pago"],
        ["Terraform State", "S3 versionado + criptografado + TLS obrigatório + lock nativo", "Recuperação de versões e bloqueio de execuções simultâneas"],
    ], [3.0 * cm, 6.6 * cm, 7.4 * cm]))
    story.append(p("Adaptação da aplicação para dois servidores", H2))
    story += bullets([
        "MONGO_HOST passou de <i>mongodb</i> (DNS do compose) para o <b>IP privado fixo 10.20.2.10</b> definido no Terraform.",
        "Senhas entregues como <b>arquivos 0400</b> montados em /run/secrets (variáveis *_FILE), alimentados pelos GitHub Secrets.",
        "Ordem de inicialização garantida pelo playbook: banco saudável -> API saudável -> frontend (healthchecks).",
        "Contêiner da API mantém o nome <b>api</b>, exigido pelo nginx.conf original; nenhum arquivo da aplicação foi alterado.",
    ])

    # ---------------- 4. pipelines
    story.append(PageBreak())
    story.append(p("4. Pipelines e parâmetros", H1))
    story.append(table([
        ["Pipeline", "Função", "Disparo"],
        ["0 · CI", "terraform fmt/validate, ansible syntax-check + lint, actionlint, shellcheck, gitleaks", "push / PR"],
        ["1 · App CI/CD", "testes da aplicação, build com os Dockerfiles originais, publicação no GHCR, deploy da tag", "manual ou chamado pelo 2"],
        ["2 · Infra - Provisionar / Atualizar", "parâmetros -> Terraform (init, fmt, validate, plan, apply) -> inventário -> Ansible -> smoke + isolamento", "manual"],
        ["3 · Operação", "health, smoke-test, logs, restart, backup, list-backups, restore (confirmação), deploy-app", "manual"],
        ["8 · Diagnóstico", "testa permissões da conta AWS por região sem criar VMs", "manual"],
        ["9 · Desativar", "backup final + terraform destroy (confirmação DESTRUIR-&lt;amb&gt;)", "manual"],
    ], [4.2 * cm, 9.8 * cm, 3.0 * cm]))
    story.append(Spacer(1, 6))
    story.append(table([
        ["Parâmetro", "Destino", "Efeito na infraestrutura / configuração"],
        ["environment", "Terraform + Ansible", "state separado (kubeshop/&lt;amb&gt;), VPC própria, nomes e tags"],
        ["run_mode", "pipeline", "plan = só validar e planejar; apply = aplicar"],
        ["instance_name", "TF_VAR_instance_name", "nome das VMs &lt;nome&gt;-&lt;amb&gt;-app / -db"],
        ["instance_type", "TF_VAR_app_instance_type", "tipo da VM da aplicação (alteração in-place)"],
        ["db_instance_type", "TF_VAR_db_instance_type", "tipo da VM do banco (dados no EBS)"],
        ["db_volume_gb", "Terraform + Ansible", "amplia o EBS online e o xfs_growfs expande o disco"],
        ["docker_image / docker_tag", "Ansible (-e)", "baixa a imagem e recria os contêineres de forma controlada"],
        ["update_os", "Ansible (-e)", "apt dist-upgrade e reinício só se o SO pedir"],
        ["extra_packages", "Ansible (-e)", "instala pacotes adicionais (ex.: htop, tree)"],
    ], [3.6 * cm, 4.4 * cm, 9.0 * cm]))
    story.append(p("Integração Terraform + Ansible", H2))
    story.append(p("O job Terraform publica os outputs (IPs, IDs, bucket) como artefato. O job Ansible os converte em inventário "
                   "(scripts/gen-inventory.sh), abre SSH na porta 22 <b>somente para o IP do runner</b>, configura a VM do banco "
                   "<b>por salto</b> através da VM da aplicação e, ao final, remove a regra temporária (if: always()). "
                   "A pipeline usa <i>set -euo pipefail</i> e dependências entre jobs: qualquer erro interrompe a execução."))
    story.append(table([
        ["Role Ansible", "Responsabilidade"],
        ["os_updates", "atualiza o SO quando update_os=true; reinicia só se /var/run/reboot-required existir"],
        ["packages", "pacotes base + extra_packages; horário via Amazon Time Sync"],
        ["hardening", "SSH só por chave, sem root, AllowUsers; unattended-upgrades"],
        ["nat_instance", "NAT da sub-rede privada (iptables + serviço systemd idempotente)"],
        ["docker", "Docker Engine oficial (só instala se faltar), rotação de logs, live-restore"],
        ["data_volume", "formata (se vazio), monta e expande o EBS; Docker exige o volume montado"],
        ["mongodb", "MongoDB autenticado, usuário da aplicação com readWrite, porta só no IP privado"],
        ["backup", "AWS CLI, scripts kubeshop-backup/restore, timer systemd diário"],
        ["containers", "API e frontend com tag explícita, pull controlado, login/logout no registro"],
        ["verify", "serviços e contêineres saudáveis, loja, API+banco, recusa sem senha, porta 27017"],
    ], [3.4 * cm, 13.6 * cm]))

    # ---------------- 5. evidências
    story.append(PageBreak())
    story.append(p("5. Evidências de execução", H1))
    story.append(p("Cenário 1 · Criação inicial", H2))
    story.append(p(f"Parâmetros: environment=dev, instance_type=t3.micro, db_instance_type=t3.small, docker_tag=1.0.0, "
                   f"update_os=true, extra_packages=htop. Imagens 1.0.0 construídas automaticamente pelo CI/CD da "
                   f"aplicação ({run('img')}); provisionamento e configuração em {run('c1')}."))
    if c1:
        plan = read(f"{c1.name}/terraform-dev-3/plan.txt")
        res = [ln.strip()[2:] for ln in plan.splitlines() if ln.strip().startswith("# aws_") and "will be created" in ln]
        res = [r.replace(" will be created", "") for r in res]
        half = (len(res) + 1) // 2
        cols = "\n".join(f"{a:<52}{b}" for a, b in zip(res[:half], res[half:] + [""]))
        summary = [ln for ln in plan.splitlines() if ln.startswith("Plan:")]
        apply_ = [ln for ln in read(f"{c1.name}/terraform-dev-3/apply.txt").splitlines() if "Apply complete" in ln]
        story += code(cols + "\n\n" + "\n".join(summary + apply_), "Terraform plan/apply (terraform-dev-3/plan.txt e apply.txt)")
        story += code(read(f"{c1.name}/ansible-dev-3/recap.txt"), "Ansible · PLAY RECAP (ansible-dev-3/recap.txt)")
        story += code(read(f"{c1.name}/ansible-dev-3/smoke.txt") + "\n" + read(f"{c1.name}/ansible-dev-3/isolation.txt"),
                      "Testes automáticos pela internet: funcionamento e isolamento do banco (ACE-03)")
    story.append(p("Verificações do Ansible na mesma execução: <i>Mongo sem senha: RECUSADO:Unauthorized</i>; "
                   "<i>Escuta 27017: somente 10.20.2.10</i>; <i>MongoDB: healthy (mongo:8.0.17)</i>; "
                   "<i>Volume de dados: /dev/nvme1n1 9.9G</i>; <i>Timer de backup: active</i>.", SMALL))
    story += image(IMG / "run-cenario1.png", 15.5, "Figura 2 · Execução do Cenário 1 no GitHub Actions (Success).")

    story.append(PageBreak())
    story.append(p("Aplicação funcionando (ACE-04)", H2))
    story.append(p("Pedido fictício criado pela interface e consultado em <i>Meus pedidos</i> após recarregar o navegador. "
                   "O mesmo pedido (#1ed462) foi usado para comprovar a persistência nos testes seguintes."))
    story += image(IMG / "loja-meus-pedidos.png", 16.5, f"Figura 3 · KubeShop em {LOJA} com o pedido #1ed462 (interface original).")

    story.append(p("Cenário 2 · Atualização do ambiente", H2))
    story.append(p(f"Parâmetros alterados: instance_type t3.micro -> <b>t3.small</b> (Terraform), docker_tag 1.0.0 -> <b>1.1.0</b> "
                   f"e extra_packages htop -> <b>htop, tree</b> (Ansible), update_os=false. Execução {run('c2')}."))
    if c2:
        plan2 = read(f"{c2.name}/terraform-dev-4/plan.txt").splitlines()
        keep = [ln for ln in plan2 if re.search(r"# aws_instance\.app|~ instance_type|^Plan:", ln)]
        keep = list(dict.fromkeys(keep))
        ap2 = [ln for ln in read(f"{c2.name}/terraform-dev-4/apply.txt").splitlines() if "Apply complete" in ln]
        story += code("\n".join(keep + ap2), "Terraform: atualização in-place, sem recriar a VM")
        log2 = re.sub(r"\x1b\[[0-9;]*m", "", read(f"{c2.name}/ansible-dev-4/ansible.log"))
        changed, cur = [], None
        for ln in log2.splitlines():
            if ln.startswith("TASK ["):
                cur = ln.split("]")[0] + "]"
            elif ln.startswith("changed:") and cur and cur not in changed:
                changed.append(cur)
        story += code(read(f"{c2.name}/ansible-dev-4/recap.txt") + "\nTarefas que alteraram algo:\n" + "\n".join(changed),
                      "Ansible: manutenção (pacote novo e imagem nova)")
    story.append(table([
        ["Verificação", "Antes", "Depois"],
        ["GET /api/info", '{"version":"1.0.0"}', '{"version":"1.1.0"}'],
        ["Pedido #1ed462 (id …11ed462)", "presente", "presente (Pedidos persistidos: 1)"],
        ["Tipo da VM app", "t3.micro", "t3.small (mesma instância, mesmo IP)"],
    ], [5.0 * cm, 5.0 * cm, 7.0 * cm]))
    story += image(IMG / "run-cenario2.png", 14.5, "Figura 4 · Execução do Cenário 2: imagens 1.1.0 construídas pelo CI/CD da aplicação, Terraform e Ansible.")

    story.append(PageBreak())
    story.append(p("Cenário 3 · Reexecução sem alterações", H2))
    story.append(p(f"Mesmos parâmetros do Cenário 2. Execução {run('c3')}."))
    if c3:
        no = [ln for ln in read(f"{c3.name}/terraform-dev-5/plan.txt").splitlines() if "No changes" in ln]
        story += code("\n".join(no) + "\n\n" + read(f"{c3.name}/ansible-dev-5/recap.txt"),
                      "Terraform sem alterações e Ansible idempotente (changed=0)")
    story += image(IMG / "run-cenario3.png", 14.5, "Figura 5 · Execução do Cenário 3.")

    story.append(p("Operação e recuperação de dados (ACE-05, ACE-07)", H2))
    story.append(table([
        ["Rotina (pipeline 3)", "Resultado registrado", "Execução"],
        ["health", "RECUSADO:Unauthorized · pedidos persistidos 1 · timer de backup active", run("health")],
        ["restart (all)", "banco -> API -> frontend saudáveis; pedido preservado", run("restart")],
        ["backup", "BACKUP_OK key=dev/kubeshop-dev-20261126T182734Z.archive.gz orders=1 bytes=492 sha256=8593120f…", run("backup")],
        ["smoke-test", "POST /api/orders -> 201 (pedido extra …7a518d54); histórico com 2 pedidos", run("smoke")],
        ["list-backups", "dev/kubeshop-dev-20261126T182734Z.archive.gz · 1 pedido · 492 B", run("list")],
        ["restore (latest, RESTAURAR)", "RESTORE_OK sha256=OK pedidos_antes=2 pedidos_backup=1 pedidos_depois=1 "
                                        "(sobrou apenas o pedido #1ed462)", run("restore")],
    ], [3.6 * cm, 10.2 * cm, 3.2 * cm]))
    story.append(Spacer(1, 6))
    story += image(IMG / "run-restore.png", 14.5, "Figura 6 · Restauração verificada (pipeline 3 · restore).")

    story.append(PageBreak())
    story.append(p("Histórico de execuções (ACE-08)", H2))
    story.append(p("Todas as mudanças foram feitas pelos pipelines; cada execução mantém logs e artefatos por 90 dias. "
                   "As duas primeiras execuções do pipeline 2 pararam antes de criar recursos (restrição de região do plano "
                   "Free e uma tag inválida no bucket de backups), ambas corrigidas por commits registrados no histórico."))
    story += image(IMG / "actions-lista.png", 15.5, "Figura 7 · Histórico do GitHub Actions do repositório.")

    # ---------------- 6. custos
    story.append(PageBreak())
    story.append(p("6. Estimativa mensal de custos (ACE-09)", H1))
    story.append(p("Premissas: AWS us-east-2, USD, preços On-Demand de tabela (referência 26/11/2026), 730 h/mês, 1 ambiente "
                   "ligado 24×7, até 100 GB/mês de tráfego de saída. Confirmar na AWS Pricing Calculator antes de decisões."))
    story.append(table([
        ["Item", "Dimensionamento", "Preço unitário", "USD/mês"],
        ["VM aplicação", "1 × t3.micro (Cenário 2: t3.small)", "US$ 0,0104/h", "7,59"],
        ["VM MongoDB", "1 × t3.small", "US$ 0,0208/h", "15,18"],
        ["Discos do SO", "2 × 20 GiB gp3", "US$ 0,08/GiB-mês", "3,20"],
        ["Dados do MongoDB", "1 × 10 GiB gp3", "US$ 0,08/GiB-mês", "0,80"],
        ["IPv4 público (EIP)", "1 endereço", "US$ 0,005/h", "3,65"],
        ["S3 (backups + state)", "&lt; 1 GB, versionado", "US$ 0,023/GB-mês", "&lt; 0,10"],
        ["Tráfego, VPC, SGs, endpoint S3, IAM", "faixa gratuita / sem custo", "—", "0,00"],
        ["GitHub Actions", "repositório público", "—", "0,00"],
        ["<b>Total</b>", "", "", "<b>~ 30,50</b>"],
    ], [5.0 * cm, 5.4 * cm, 3.6 * cm, 3.0 * cm]))
    story.append(Spacer(1, 6))
    story += bullets([
        "Com a VM app em t3.small (estado após o Cenário 2): ~ US$ 38/mês.",
        "Economias: NAT pela VM app em vez de NAT Gateway (-US$ 32,85), endpoint S3 gratuito, banco sem IP público, sem Load Balancer.",
        "Créditos (separados do custo recorrente): a conta está no plano Free com US$ 100 de crédito válido até 26/05/2027; "
        "após os créditos, vale o custo recorrente acima.",
        "Recursos que continuam cobrando após a desativação: apenas os buckets S3 de backup e de state (centavos/mês).",
    ])

    # ---------------- 7. aceite
    story.append(p("7. Critérios de aceite e de avaliação", H1))
    story.append(table([
        ["Critério", "Evidência"],
        ["ACE-01 Reprodução", "Ambiente criado do zero pelo pipeline 2 (" + run("c1") + "); pré-requisitos em docs/00"],
        ["ACE-02 Duas VMs", "Inventário: kubeshop-dev-app e kubeshop-dev-db (sem IP público)"],
        ["ACE-03 Isolamento", "ISOLATION_RESULT=PASS, RECUSADO:Unauthorized, escuta só em 10.20.2.10"],
        ["ACE-04 Aplicação", "Figura 3 (pedido consultado após recarregar) + smoke-test"],
        ["ACE-05 Persistência", "Pedido preservado após restart e após a alteração de instance_type (Cenário 2)"],
        ["ACE-06 CI/CD", "Pipeline 1 (testes, build, GHCR) chamado automaticamente pelo 2; deploy por tag (docs/04)"],
        ["ACE-07 Recuperação", "Timer de backup diário ativo; backup + restore com conferência de pedidos e SHA-256"],
        ["ACE-08 Administração", "Histórico do Actions (Figura 7), docs/03; credenciais só em Secrets"],
        ["ACE-09 Custos", "Seção 6 e docs/02"],
        ["ACE-10 Transferência", "README e docs 00 a 07; tags Project=KubeShop em todos os recursos"],
    ], [4.0 * cm, 13.0 * cm]))
    story.append(Spacer(1, 6))
    story.append(table([
        ["Critério PM-04 (pontos)", "Onde está"],
        ["Pipeline funcional com parâmetros dinâmicos (2,0)", "Seção 4: 10 parâmetros, cada um alterando infra ou configuração"],
        ["Provisionamento e atualização com Terraform (2,0)", "Cenários 1-3: init/plan/apply na pipeline, state remoto, alteração in-place"],
        ["Configuração e manutenção com Ansible (2,0)", "Roles (seção 4); pacote e imagem atualizados no Cenário 2; changed=0 no Cenário 3"],
        ["Adequação ao documento de demanda (1,5)", "Seções 2 e 3"],
        ["Integração Terraform + Ansible e testes (1,5)", "Seção 4 (inventário gerado) e seção 5"],
        ["Documentação e explicação técnica (1,0)", "Este documento + README e docs/ no repositório"],
    ], [7.0 * cm, 10.0 * cm]))

    # ---------------- 8. segurança, limitações
    story.append(p("8. Segurança, limitações e operação posterior", H1))
    story += bullets([
        "<b>Segredos:</b> AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY, SSH_PRIVATE_KEY, MONGO_ROOT_PASSWORD e MONGO_APP_PASSWORD existem "
        "apenas como GitHub Secrets (senhas geradas aleatoriamente pelo script de setup, nunca exibidas). Mascarados nos logs; "
        "tarefas com senha usam no_log; docker inspect mostra só *_PASSWORD_FILE.",
        "<b>Limitações:</b> instância única de cada serviço (sem alta disponibilidade); RPO de 24 h no backup diário (backup sob "
        "demanda disponível); HTTP sem TLS por ausência de domínio; NAT na VM app (se ela cair, o banco perde só a saída para atualizações).",
        "<b>Operação:</b> rotinas diárias (health, logs, restart, backup) separadas das destrutivas (restore com confirmação "
        "RESTAURAR e desativação com DESTRUIR-&lt;amb&gt;), descritas no manual docs/03-manual-operacao.md.",
        "<b>Desativação:</b> pipeline 9 faz backup final e terraform destroy; permanecem apenas os buckets de backup e de state.",
    ])
    story.append(Spacer(1, 10))
    story.append(p("Repositório com código, pipelines, documentação completa e artefatos das execuções: " + link(REPO), BODY))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                            bottomMargin=1.8 * cm, title="PM-04 · KubeShop na AWS",
                            author=", ".join(INTEGRANTES), subject="Projeto Final PM-04 - Terraform, Ansible e CI/CD")
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF gerado: {OUT}")


if __name__ == "__main__":
    build()
