# from semantics_cbv_weak import reduce_cbv_weak_sync as reduce_cbv_weak_sync
# from semantics_nli import reduce_nli_sync as reduce_nli_sync
# from semantics_sequential import reduce_sequential_sync as reduce_sequential_sync
from .graph_semantics import (
    reduce_graph_opportunistic as reduce_graph_opportunistic,
    reduce_graph_opportunistic_dfs as reduce_graph_opportunistic_dfs,
    reduce_graph_sequential as reduce_graph_sequential,
)