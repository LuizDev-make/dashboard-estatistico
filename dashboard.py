"""
Dashboard Estatístico — Shiny for Python
=========================================
Funcionalidades:
  1. Análise descritiva (histograma, boxplot, estatísticas)
  2. Teste de hipóteses para a média (variância conhecida)
  3. Intervalo de confiança normal para a média
  4. Regressão linear simples
"""

from shiny import App, reactive, ui, render
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import io

# ──────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────

app_ui = ui.page_navbar(
    # ── Aba 1: Análise Descritiva ──────────────
    ui.nav_panel(
        "Análise Descritiva",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_file("file1", "Selecione o arquivo de dados (CSV ou Excel)", accept=[".csv", ".xlsx", ".xls"]),
                ui.input_action_button("btn_carregar", "📂 Carregar Dados", class_="btn-primary w-100 mt-2"),
                ui.hr(),
                ui.output_ui("info_dados"),
                ui.input_select("var_quant", "Variável quantitativa", choices=[]),
                width=320,
            ),
            ui.navset_card_tab(
                ui.nav_panel(
                    "Histograma",
                    ui.output_plot("histograma", height="450px"),
                ),
                ui.nav_panel(
                    "Boxplot",
                    ui.output_plot("boxplot", height="450px"),
                ),
                ui.nav_panel(
                    "Estatísticas Descritivas",
                    ui.output_ui("estat_desc"),
                ),
                ui.nav_panel(
                    "Pré-visualização",
                    ui.output_ui("preview_dados"),
                ),
            ),
        ),
    ),

    # ── Aba 2: Teste de Hipóteses ──────────────
    ui.nav_panel(
        "Teste de Hipóteses",
        ui.layout_sidebar(
            ui.sidebar(
                ui.markdown("**Configuração do Teste Z (variância conhecida)**"),
                ui.input_numeric("var_pop", "Variância populacional (σ²)", value=1.0, min=0.0001, step=0.1),
                ui.input_radio_buttons(
                    "tipo_teste",
                    "Tipo de teste",
                    choices={
                        "bilateral": "Bilateral",
                        "right": "Unilateral à direita",
                        "left": "Unilateral à esquerda",
                    },
                ),
                ui.input_slider("mu0", "Valor de μ₀", min=-100, max=100, value=0, step=0.1),
                ui.input_slider("alpha", "Nível de significância (α)", min=0.01, max=0.20, value=0.05, step=0.01),
                width=320,
            ),
            ui.card(
                ui.card_header("Resultados do Teste de Hipóteses"),
                ui.output_ui("resultado_teste"),
            ),
        ),
    ),

    # ── Aba 3: Intervalo de Confiança ──────────
    ui.nav_panel(
        "Intervalo de Confiança",
        ui.layout_sidebar(
            ui.sidebar(
                ui.markdown("**Intervalo de Confiança Normal para a Média**"),
                ui.input_numeric("var_pop_ic", "Variância populacional (σ²)", value=1.0, min=0.0001, step=0.1),
                ui.input_slider("nivel_conf", "Nível de confiança", min=0.80, max=0.99, value=0.95, step=0.01),
                width=320,
            ),
            ui.card(
                ui.card_header("Intervalo de Confiança"),
                ui.output_ui("resultado_ic"),
            ),
        ),
    ),

    # ── Aba 4: Regressão Linear Simples ────────
    ui.nav_panel(
        "Regressão Linear",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_select("var_y", "Variável resposta (y)", choices=[]),
                ui.input_select("var_x", "Variável explicativa (x)", choices=[]),
                width=320,
            ),
            ui.navset_card_tab(
                ui.nav_panel(
                    "Gráfico de Dispersão",
                    ui.output_plot("grafico_dispersao", height="500px"),
                ),
                ui.nav_panel(
                    "Resultados da Regressão",
                    ui.output_ui("resultado_regressao"),
                ),
            ),
        ),
    ),

    title="📊 Dashboard Estatístico",
    bg="#2c3e50",
    inverse=True,
)


# ──────────────────────────────────────────────
# SERVER
# ──────────────────────────────────────────────

def server(input, output, session):

    # ── Armazena os dados carregados ─────────────
    dados_rv = reactive.value(None)

    # ── Leitura do arquivo ao clicar no botão ──
    @reactive.effect
    @reactive.event(input.btn_carregar)
    def _carregar_dados():
        file_info = input.file1()
        if file_info is None:
            ui.notification_show("⚠️ Selecione um arquivo antes de clicar em Carregar.", type="warning", duration=4)
            return
        file_path = file_info[0]["datapath"]
        name = file_info[0]["name"]
        try:
            if name.endswith(".csv"):
                # Tenta diferentes combinações de separador e decimal
                df = None
                tentativas = [
                    {"sep": ";", "decimal": ",", "encoding": "utf-8"},
                    {"sep": ";", "decimal": ",", "encoding": "latin-1"},
                    {"sep": ",", "decimal": ".", "encoding": "utf-8"},
                    {"sep": ",", "decimal": ".", "encoding": "latin-1"},
                    {"sep": "\t", "decimal": ",", "encoding": "utf-8"},
                ]
                for params in tentativas:
                    try:
                        df = pd.read_csv(file_path, **params)
                        if df.shape[1] > 1:
                            break
                    except Exception:
                        continue
                if df is None or df.shape[1] <= 1:
                    df = pd.read_csv(file_path, sep=None, engine="python", encoding="latin-1")
            else:
                df = pd.read_excel(file_path)

            # Tenta converter colunas que parecem numéricas mas foram lidas como texto
            import re
            cols_to_add = {}
            for col in list(df.columns):
                if df[col].dtype == object or str(df[col].dtype) == "string":
                    try:
                        # 1) Tenta conversão direta (vírgula → ponto)
                        converted = df[col].astype(str).str.replace(",", ".", regex=False)
                        converted = pd.to_numeric(converted, errors="coerce")
                        if converted.notna().sum() > len(df) * 0.5:
                            df[col] = converted
                            continue

                        # 2) Tenta extrair números de strings com unidades (ex: "5 km/h", "3.2 kg")
                        extracted = df[col].astype(str).str.extract(r"([-+]?\d+[.,]?\d*)", expand=False)
                        if extracted is not None:
                            extracted = extracted.str.replace(",", ".", regex=False)
                            extracted = pd.to_numeric(extracted, errors="coerce")
                            if extracted.notna().sum() > len(df) * 0.5:
                                df[col] = extracted
                                continue

                        # 3) Tenta separar coordenadas "lat, lon" em duas colunas
                        sample = df[col].dropna().head(5).astype(str)
                        coord_pattern = r"^\s*([-+]?\d+\.\d+)\s*,\s*([-+]?\d+\.\d+)\s*$"
                        if sample.str.match(coord_pattern).sum() >= 3:
                            parts = df[col].astype(str).str.extract(coord_pattern)
                            cols_to_add[f"{col}_lat"] = pd.to_numeric(parts[0], errors="coerce")
                            cols_to_add[f"{col}_lon"] = pd.to_numeric(parts[1], errors="coerce")
                    except Exception:
                        pass

            # Adiciona colunas extraídas de coordenadas
            for k, v in cols_to_add.items():
                df[k] = v

            dados_rv.set(df)
            num_cols = df.select_dtypes(include="number").columns.tolist()
            print(f"\n{'='*50}")
            print(f"Arquivo carregado: {name}")
            print(f"Shape: {df.shape}")
            print(f"Tipos das colunas:")
            for c in df.columns:
                print(f"  {c}: {df[c].dtype} (exemplo: {df[c].iloc[0] if len(df) > 0 else 'vazio'})")
            print(f"Colunas numéricas: {num_cols}")
            print(f"{'='*50}\n")
            ui.notification_show(
                f"✅ Arquivo '{name}' carregado! "
                f"({df.shape[0]} linhas × {df.shape[1]} colunas, "
                f"{len(num_cols)} numéricas)",
                type="message", duration=5
            )
        except Exception as e:
            print(f"ERRO ao carregar: {e}")
            import traceback
            traceback.print_exc()
            ui.notification_show(f"❌ Erro ao ler o arquivo: {e}", type="error", duration=6)

    # ── Referência reativa aos dados ───────────
    @reactive.calc
    def dados():
        return dados_rv.get()

    # ── Atualizar seletores de variáveis ───────
    @reactive.effect
    def _update_selectors():
        df = dados()
        if df is None:
            return
        # Apenas colunas numéricas
        num_cols = df.select_dtypes(include="number").columns.tolist()
        ui.update_select("var_quant", choices=num_cols, session=session)
        ui.update_select("var_y", choices=num_cols, session=session)
        ui.update_select("var_x", choices=num_cols, session=session)

    # ── Info dos dados na sidebar ──────────────
    @render.ui
    def info_dados():
        df = dados()
        if df is None:
            return ui.markdown("*Nenhum arquivo carregado.*")
        num_cols = df.select_dtypes(include="number").columns.tolist()
        all_cols_info = ""
        for c in df.columns:
            tipo = "\U0001f522" if c in num_cols else "\U0001f524"
            all_cols_info += f"- {tipo} `{c}` ({df[c].dtype})\n"
        return ui.TagList(
            ui.markdown(f"**✅ Arquivo carregado**"),
            ui.markdown(f"- Linhas: **{df.shape[0]}**"),
            ui.markdown(f"- Colunas: **{df.shape[1]}**"),
            ui.markdown(f"- Numéricas: **{len(num_cols)}**"),
            ui.markdown(f"\n**Colunas detectadas:**"),
            ui.markdown(all_cols_info),
        )

    # ── Pré-visualização dos dados ─────────────
    @render.ui
    def preview_dados():
        df = dados()
        if df is None:
            return ui.markdown("⚠️ Carregue um arquivo para visualizar os dados.")
        html_table = df.head(15).to_html(index=False, classes="table table-striped table-hover table-sm", border=0)
        return ui.TagList(
            ui.markdown(f"**Primeiras 15 linhas** ({df.shape[0]} linhas no total)"),
            ui.HTML(html_table),
        )

    # ── Vetor da variável selecionada ──────────
    @reactive.calc
    def vetor_var():
        df = dados()
        var = input.var_quant()
        if df is None or var == "" or var not in df.columns:
            return None
        return df[var].dropna()

    # ────────────────────────────────────────────
    # 1. ANÁLISE DESCRITIVA
    # ────────────────────────────────────────────

    @render.plot
    def histograma():
        v = vetor_var()
        if v is None or len(v) == 0:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "Carregue um arquivo e selecione uma variável",
                    ha="center", va="center", fontsize=13, color="gray")
            ax.set_axis_off()
            return fig
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.hist(v, bins="auto", color="#3498db", edgecolor="white", alpha=0.85)
        ax.set_title(f"Histograma — {input.var_quant()}", fontsize=14, fontweight="bold")
        ax.set_xlabel(input.var_quant())
        ax.set_ylabel("Frequência")
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        return fig

    @render.plot
    def boxplot():
        v = vetor_var()
        if v is None or len(v) == 0:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "Carregue um arquivo e selecione uma variável",
                    ha="center", va="center", fontsize=13, color="gray")
            ax.set_axis_off()
            return fig
        fig, ax = plt.subplots(figsize=(8, 4.5))
        bp = ax.boxplot(v, vert=True, patch_artist=True,
                        boxprops=dict(facecolor="#2ecc71", alpha=0.7),
                        medianprops=dict(color="#c0392b", linewidth=2))
        ax.set_title(f"Boxplot — {input.var_quant()}", fontsize=14, fontweight="bold")
        ax.set_ylabel(input.var_quant())
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        return fig

    @render.ui
    def estat_desc():
        v = vetor_var()
        if v is None or len(v) == 0:
            return ui.markdown("⚠️ Carregue um arquivo e selecione uma variável.")
        resumo = pd.DataFrame({
            "Estatística": ["Média", "Mediana", "Desvio-padrão", "Tamanho da amostra (n)", "Valor mínimo", "Valor máximo"],
            "Valor": [
                f"{v.mean():.4f}",
                f"{v.median():.4f}",
                f"{v.std(ddof=1):.4f}",
                f"{len(v)}",
                f"{v.min():.4f}",
                f"{v.max():.4f}",
            ],
        })
        html_table = resumo.to_html(index=False, classes="table table-striped table-hover", border=0)
        return ui.HTML(html_table)

    # ────────────────────────────────────────────
    # 2. TESTE DE HIPÓTESES (Z – variância conhecida)
    # ────────────────────────────────────────────

    @render.ui
    def resultado_teste():
        v = vetor_var()
        if v is None or len(v) == 0:
            return ui.markdown("⚠️ Carregue um arquivo e selecione uma variável na aba *Análise Descritiva*.")

        n = len(v)
        x_bar = v.mean()
        sigma = np.sqrt(input.var_pop())
        mu0 = input.mu0()
        alpha = input.alpha()
        tipo = input.tipo_teste()

        z_calc = (x_bar - mu0) / (sigma / np.sqrt(n))

        if tipo == "bilateral":
            p_valor = 2 * (1 - stats.norm.cdf(abs(z_calc)))
            z_crit = stats.norm.ppf(1 - alpha / 2)
            regra = f"|Z| > {z_crit:.4f}"
            rejeita = abs(z_calc) > z_crit
            hipoteses = f"H₀: μ = {mu0}  vs  H₁: μ ≠ {mu0}"
        elif tipo == "right":
            p_valor = 1 - stats.norm.cdf(z_calc)
            z_crit = stats.norm.ppf(1 - alpha)
            regra = f"Z > {z_crit:.4f}"
            rejeita = z_calc > z_crit
            hipoteses = f"H₀: μ ≤ {mu0}  vs  H₁: μ > {mu0}"
        else:  # left
            p_valor = stats.norm.cdf(z_calc)
            z_crit = stats.norm.ppf(alpha)
            regra = f"Z < {z_crit:.4f}"
            rejeita = z_calc < z_crit
            hipoteses = f"H₀: μ ≥ {mu0}  vs  H₁: μ < {mu0}"

        decisao = "✅ **Rejeitar H₀**" if rejeita else "❌ **Não rejeitar H₀**"
        cor = "danger" if rejeita else "success"

        return ui.TagList(
            ui.markdown(f"### {hipoteses}"),
            ui.layout_columns(
                ui.value_box("Estatística Z", f"{z_calc:.4f}", theme="primary"),
                ui.value_box("p-valor", f"{p_valor:.6f}", theme="info"),
                ui.value_box("Decisão", "Rejeitar H₀" if rejeita else "Não rejeitar H₀", theme=cor),
                col_widths=[4, 4, 4],
            ),
            ui.markdown(f"""
**Detalhes:**
- Média amostral (x̄): **{x_bar:.4f}**
- μ₀: **{mu0}**
- σ² (informada): **{input.var_pop()}**
- n: **{n}**
- α: **{alpha}**
- Regra de decisão: Rejeitar H₀ se {regra}
"""),
        )

    # ────────────────────────────────────────────
    # 3. INTERVALO DE CONFIANÇA
    # ────────────────────────────────────────────

    @render.ui
    def resultado_ic():
        v = vetor_var()
        if v is None or len(v) == 0:
            return ui.markdown("⚠️ Carregue um arquivo e selecione uma variável na aba *Análise Descritiva*.")

        n = len(v)
        x_bar = v.mean()
        sigma = np.sqrt(input.var_pop_ic())
        gamma = input.nivel_conf()
        z_gamma = stats.norm.ppf((1 + gamma) / 2)
        margem = z_gamma * (sigma / np.sqrt(n))
        li = x_bar - margem
        ls = x_bar + margem

        return ui.TagList(
            ui.layout_columns(
                ui.value_box("Limite Inferior", f"{li:.4f}", theme="primary"),
                ui.value_box("Média Amostral", f"{x_bar:.4f}", theme="info"),
                ui.value_box("Limite Superior", f"{ls:.4f}", theme="primary"),
                col_widths=[4, 4, 4],
            ),
            ui.markdown(f"""
**Detalhes do Intervalo de Confiança:**
- Nível de confiança: **{gamma * 100:.0f}%**
- z crítico: **{z_gamma:.4f}**
- Margem de erro: **{margem:.4f}**
- σ² (informada): **{input.var_pop_ic()}**
- n: **{n}**

**IC({gamma * 100:.0f}%) = [{li:.4f} ; {ls:.4f}]**
"""),
        )

    # ────────────────────────────────────────────
    # 4. REGRESSÃO LINEAR SIMPLES
    # ────────────────────────────────────────────

    @render.plot
    def grafico_dispersao():
        df = dados()
        var_x = input.var_x()
        var_y = input.var_y()
        if df is None or var_x == "" or var_y == "" or var_x not in df.columns or var_y not in df.columns:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "Carregue um arquivo e selecione as variáveis x e y",
                    ha="center", va="center", fontsize=13, color="gray")
            ax.set_axis_off()
            return fig

        x = df[var_x].dropna()
        y = df[var_y].dropna()
        # Alinhar os vetores
        mask = df[[var_x, var_y]].dropna()
        x = mask[var_x].values
        y = mask[var_y].values

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(x, y, alpha=0.6, color="#3498db", edgecolor="white", s=50, label="Dados")

        x_line = np.linspace(x.min(), x.max(), 200)
        y_line = intercept + slope * x_line
        ax.plot(x_line, y_line, color="#e74c3c", linewidth=2.5, label=f"ŷ = {intercept:.4f} + {slope:.4f}x")

        ax.set_xlabel(var_x, fontsize=12)
        ax.set_ylabel(var_y, fontsize=12)
        ax.set_title(f"Dispersão e Regressão: {var_y} ~ {var_x}", fontsize=14, fontweight="bold")
        ax.legend(fontsize=11)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        return fig

    @render.ui
    def resultado_regressao():
        df = dados()
        var_x = input.var_x()
        var_y = input.var_y()
        if df is None or var_x == "" or var_y == "" or var_x not in df.columns or var_y not in df.columns:
            return ui.markdown("⚠️ Carregue um arquivo e selecione as variáveis x e y.")

        mask = df[[var_x, var_y]].dropna()
        x = mask[var_x].values
        y = mask[var_y].values

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        r2 = r_value ** 2

        sinal = "+" if slope >= 0 else "-"

        return ui.TagList(
            ui.layout_columns(
                ui.value_box("Correlação (R)", f"{r_value:.4f}", theme="primary"),
                ui.value_box("Determinação (R²)", f"{r2:.4f}", theme="info"),
                ui.value_box("p-valor (inclinação)", f"{p_value:.6f}", theme="warning"),
                col_widths=[4, 4, 4],
            ),
            ui.markdown(f"""
### Equação da Reta Ajustada

**ŷ = {intercept:.4f} {sinal} {abs(slope):.4f} · x**

---

**Detalhes:**
- Intercepto (β₀): **{intercept:.4f}**
- Inclinação (β₁): **{slope:.4f}**
- Erro-padrão da inclinação: **{std_err:.4f}**
- Coeficiente de correlação (R): **{r_value:.4f}**
- Coeficiente de determinação (R²): **{r2:.4f}**
- n (observações válidas): **{len(x)}**
"""),
        )


# ──────────────────────────────────────────────
# APP
# ──────────────────────────────────────────────

app = App(app_ui, server)
