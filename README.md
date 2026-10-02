# Radial Launcher

Launcher radial para Windows, ativado por `Win + '`.

## Requisitos

- Windows 10/11
- Python 3.11 ou superior
- PySide6

## Instalação

Execute `install.bat`.

Depois execute `run.bat`.

O programa fica na bandeja do Windows e registra globalmente:

`Win + '`

## Como usar

1. Pressione `Win + '`.
2. Mova o mouse para o aplicativo desejado.
3. Solte o botão esquerdo ou clique no aplicativo.
4. O programa será aberto.

Também é possível usar as teclas `1` a `8` enquanto a roda estiver aberta.

`ESC` fecha a roda.

## Configuração

Edite `config.json`.

Cada item possui:

- `name`: nome exibido na roda.
- `path`: caminho do executável, atalho `.lnk`, pasta ou comando.

Exemplo:

```json
{
    "name": "Chrome",
    "path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
}
```

Depois de salvar o JSON, abra a roda novamente. Não é necessário reiniciar o programa.

## Observação sobre Win + '

O programa usa a API `RegisterHotKey` do Windows com `VK_OEM_7`.

Se outro programa já estiver utilizando a combinação, o Windows pode impedir o registro do atalho.

## Próximas melhorias possíveis

- Ícones reais dos aplicativos.
- Animação da roda.
- Configurador gráfico.
- Arrastar e soltar aplicativos nos slots.
- Quantidade de slots configurável.
- Submenus.
- Perfis diferentes.
- Inicialização automática com o Windows.
