# NEXA: atualização automática de notícias

1. Crie um repositório no GitHub e carregue todo o conteúdo desta pasta (incluindo a pasta `.github`).
2. Reveja `fontes.json`: já inclui 12 feeds. Confirme os termos de utilização de cada um, remova os que não quiser e ajuste a credibilidade (`v` verde, `a` amarelo, `x` vermelho). Com `"so_politica": true`, só entram notícias com palavras ligadas à política.
3. Em Settings > Pages, publique a partir do ramo `main`, pasta raiz.
4. Em Actions, execute "Atualizar notícias" manualmente uma vez para testar. Depois corre sozinho todos os dias.

Notas
- O programa guarda só título, resumo curto e ligação para a fonte original.
- Se nenhuma fonte responder, o ficheiro anterior é mantido e a execução falha, para o avisar.
- A explicação por IA ("Compreender a política") só funciona dentro do Claude. Fora dele, o site mostra que a função não está disponível.
