# Validação do laboratório ECA/QCA v3.1

## Estado antes da coleta confirmatória

O código, o perfil `paper`, a Emenda 1, as cinco novas sementes e a regra simultânea Bonferroni–Hoeffding foram congelados antes da execução confirmatória definitiva. Os resultados da execução-piloto não serão reutilizados.

Este arquivo será completado em um commit posterior à coleta com os resultados da árvore congelada. Critérios: regras 30/60/90; involução de `U_F`; bases exaustivas; fidelidade `≥1−2×10⁻⁷`; TFQ×Cirq `≤2×10⁻⁵`; sementes independentes; dez artefatos SHA-256; notebook de 21 células/11 códigos e execução reentrante.

## Limitações pré-declaradas

- `U_F` não é uma QCA física infinita completa.
- TFQ reutiliza Cirq.
- O canal é lógico, não um modelo de dispositivo.
- Tempos de simulador não demonstram vantagem quântica.
- `smoke` não decide H3/H4; isso cabe ao perfil `paper` congelado.
