# Radial Launcher V2

Launcher radial configurável para Windows, com atalho global, configuração
visual e gerenciamento pela bandeja do sistema.

## Baixar e executar

Baixe `RadialLauncher.exe` na seção **Assets** da
[release mais recente](https://github.com/LucasSilvaFarias/shortcut-wheel/releases/latest)
e execute-o no Windows 10 ou 11. A versão executável não exige que Python ou
PySide6 estejam instalados.

O aplicativo permanece na bandeja do sistema. Na primeira execução, cria o
arquivo `config.json` ao lado do executável.

## Recursos

- Abra a roda com `Win + '` por padrão.
- Personalize a combinação de teclas globais.
- Configure até oito aplicativos em uma janela visual.
- Arraste arquivos para os slots ou use **Adicionar arquivo...**.
- Edite nomes e limpe slots.
- Inicie um item apontando para ele na roda ou usando as teclas `1` a `8`.
- Abra a roda, configure o programa ou saia pelo menu da bandeja.
- Salve os aplicativos e o atalho em `config.json`.

## Configuração

Clique com o botão direito no ícone do Radial Launcher na bandeja e selecione
**Configurar**. Adicione executáveis, atalhos `.lnk`, arquivos `.bat` ou `.cmd`;
arraste-os para um slot ou use o seletor de arquivos. Selecione pelo menos um
modificador (`Win`, `Ctrl`, `Alt` ou `Shift`) e a tecla desejada, então clique
em **Salvar e aplicar**.

Também é possível editar `config.json` diretamente. Cada item usa `name` para o
nome exibido e `path` para o caminho do aplicativo. A configuração é lida
novamente ao abrir a roda.

Se o Windows não registrar o atalho escolhido, ele pode estar em uso por outro
programa. Selecione outra combinação na janela de configuração.

## Executar a partir do código-fonte

Requisitos: Windows 10/11 e Python 3.11 ou superior.

1. Execute `install.bat` para instalar o PySide6.
2. Execute `run.bat` para iniciar o aplicativo.

## Gerar o executável

Com o Python Launcher instalado, execute `build_exe.bat`. O script instala as
dependências de build e cria:

```text
dist\RadialLauncher.exe
```

O executável é criado em modo one-file e inclui o ícone do aplicativo. O
`config.json` fica fora do executável para que as configurações possam ser
alteradas e preservadas entre execuções.
