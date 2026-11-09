# Proteções do servidor do NR-1 Map (cópia de referência)

Estes arquivos são a cópia das proteções que ficam no servidor (projeto Firebase `entrevista-inicial`, região `southamerica-east1`). Eles estão aqui para a equipe de segurança poder revisar. **Não contêm senhas nem chaves.**

- `regras-nr1map.rules.txt` — trecho das regras do banco (Firestore) do NR-1 Map. Quem é quem vem de "marcas" na conta (administradora, empresa, usuário, parceiro; colaborador, RH, gestor), colocadas só pelo servidor. Empresa só lê a própria empresa; o resto é negado por padrão.
- `functions/index.js` — `marcarPapel` (marca o papel da conta, só o servidor) e lembretes.
- `functions/colab.js` — `colabEntrar` / `colabEnviar` / `colabSugestao` / `colabChamado`: o colaborador entra com o código; a resposta é gravada sem identificar quem respondeu.
- `functions/aceite.js` — assinatura de aceite. `functions/cadastro.js` — cadastro de empresa.

As funções públicas do site (`receberLead` e `receberDepoimento`) estão em `functions/index.js` na raiz do repositório, já com validação, limite por IP e por e-mail e liberação só para `https://nr1-maps.com.br`.

Última revisão: 09/11/2026.
