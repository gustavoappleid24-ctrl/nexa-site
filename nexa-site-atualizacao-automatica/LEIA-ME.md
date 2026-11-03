# NEXA: atualização automática de notícias

1. Crie um repositório no GitHub e carregue todo o conteúdo desta pasta (incluindo a pasta `.github`).
2. Edite `fontes.json`: substitua os exemplos pelos feeds RSS das fontes que aprovou e indique a credibilidade de cada uma (`v` verde, `a` amarelo, `x` vermelho). Confirme os termos de utilização de cada feed.
3. Em Settings > Pages, publique a partir do ramo `main`, pasta raiz.
4. Em Actions, execute "Atualizar notícias" manualmente uma vez para testar. Depois corre sozinho todos os dias.

Notas
- O programa guarda só título, resumo curto e ligação para a fonte original.
- Se nenhuma fonte responder, o ficheiro anterior é mantido e a execução falha, para o avisar.
- A explicação por IA ("Compreender a política") só funciona dentro do Claude. Fora dele, o site mostra que a função não está disponível.
