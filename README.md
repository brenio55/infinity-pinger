# InfinityPinger

**InfinityPinger** é uma ferramenta de monitoramento e diagnóstico de rede de código aberto (Open Source), projetada como uma alternativa leve, rápida e multiplataforma a grandes softwares pagos do mercado. Desenvolvida e mantida pela **Orkestrae**, a ferramenta foca em fornecer uma interface limpa e análises precisas da latência da rede e perda de pacotes ao longo do tempo.

![InfinityPinger Logo](logo.png)

## 🚀 Principais Funcionalidades

*   **Monitoramento Multi-Host:** Adicione e monitore múltiplos endereços IP ou domínios simultaneamente com uma interface de threads otimizada.
*   **Gráficos Avançados (Stairs/Steps):** Visualização profissional de latência utilizando gráficos em formato "step", o que permite identificar exatamente os saltos e inconsistências de resposta.
*   **Identificação de Perda de Pacotes (LOZ):** Trechos onde ocorrem perdas de pacote (Loss of Signal/Zone) são automaticamente destacados com um fundo vermelho escuro (LOZ) direto no gráfico.
*   **Janelas de Tempo Dinâmicas:** Alterne a visualização de gráficos com janelas que vão desde os últimos **30 segundos até 24 horas**. O eixo de tempo (timeline) na base do gráfico adapta inteligentemente seus "ticks" para qualquer formato.
*   **Controle Individual:** Botões de `Start` e `Stop` granulares em cada host na sidebar, permitindo que você pause temporariamente a coleta de um IP específico sem interferir nos demais.
*   **Responsividade UI:** Interface Flat e minimalista feita em *CustomTkinter*. Os gráficos se ajustam à altura da janela sem scrollbars ocultas desnecessárias.
*   **Exportação de Relatórios:** Gere PDFs profissionais, gráficos estáticos em PNG ou extraia os logs brutos em CSV.

## 🛠️ Tecnologias Utilizadas

*   **Python 3.10+**
*   **CustomTkinter** (para a GUI moderna)
*   **Matplotlib** (para os subplots gráficos de alta performance)
*   **ReportLab** (para a geração de relatórios PDF)

## 📦 Instalação e Uso

1. Clone o repositório:
```bash
git clone https://github.com/orkestrae/InfinityPinger.git
cd InfinityPinger
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute o aplicativo:
```bash
python main.py
```

## 🏢 Sobre a Orkestrae

**Orkestrae** é uma empresa dedicada ao desenvolvimento de softwares robustos e inovadores. Acreditamos no open-source e na construção de ferramentas que capacitam administradores de rede, desenvolvedores e engenheiros a visualizar dados complexos da forma mais simples possível.

## 📄 Licença

Este projeto é de código aberto e distribuído sob a Licença MIT. Sinta-se à vontade para fazer forks, criar novas issues e submeter Pull Requests!
