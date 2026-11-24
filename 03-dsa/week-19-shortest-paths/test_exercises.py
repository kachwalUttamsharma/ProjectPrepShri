import random

import pytest

from exercises import *


# ---------- dijkstra_distances ----------
def test_dijkstra_basic():
    edges = [(0, 1, 4), (0, 2, 1), (2, 1, 2), (1, 3, 1)]
    assert dijkstra_distances(4, edges, 0) == [0, 3, 1, 4]


def test_dijkstra_unreachable_and_directed():
    d = dijkstra_distances(3, [(0, 1, 5)], 0)
    assert d == [0, 5, INF]
    assert dijkstra_distances(3, [(0, 1, 5)], 1) == [INF, 0, INF]


def test_dijkstra_single_node_no_edges():
    assert dijkstra_distances(1, [], 0) == [0]


def test_dijkstra_zero_weights_parallel_and_self_loops():
    edges = [(0, 1, 0), (0, 1, 7), (1, 1, 3), (1, 2, 0), (0, 2, 5)]
    assert dijkstra_distances(3, edges, 0) == [0, 0, 0]


def test_dijkstra_matches_floyd_warshall_random():
    rng = random.Random(1)
    for _ in range(40):
        n = rng.randint(1, 8)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(0, 9)) for _ in range(rng.randint(0, 20))]
        fw = [[INF] * n for _ in range(n)]
        for i in range(n):
            fw[i][i] = 0
        for u, v, w in edges:
            fw[u][v] = min(fw[u][v], w)
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    fw[i][j] = min(fw[i][j], fw[i][k] + fw[k][j])
        src = rng.randrange(n)
        assert dijkstra_distances(n, edges, src) == fw[src]


# ---------- shortest_path_binary_matrix ----------
def test_binary_matrix_examples():
    assert shortest_path_binary_matrix([[0, 1], [1, 0]]) == 2
    assert shortest_path_binary_matrix([[0, 0, 0], [1, 1, 0], [1, 1, 0]]) == 4


def test_binary_matrix_blocked():
    assert shortest_path_binary_matrix([[1, 0, 0], [1, 1, 0], [1, 1, 0]]) == -1
    assert shortest_path_binary_matrix([[0, 0], [0, 1]]) == -1
    assert shortest_path_binary_matrix([[0, 1], [1, 1]]) == -1


def test_binary_matrix_tiny():
    assert shortest_path_binary_matrix([[0]]) == 1
    assert shortest_path_binary_matrix([[1]]) == -1


def test_binary_matrix_open_diagonal_and_snake():
    assert shortest_path_binary_matrix([[0] * 5 for _ in range(5)]) == 5
    assert shortest_path_binary_matrix([[0, 1, 0], [1, 0, 0], [0, 0, 0]]) == 3
    assert shortest_path_binary_matrix([[0, 0, 0, 0], [1, 1, 1, 0], [0, 0, 0, 0], [0, 1, 1, 1]]) == -1


# ---------- network_delay_time ----------
def test_network_delay_examples():
    assert network_delay_time([[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2) == 2
    assert network_delay_time([[1, 2, 1]], 2, 1) == 1
    assert network_delay_time([[1, 2, 1]], 2, 2) == -1


def test_network_delay_single_node():
    assert network_delay_time([], 1, 1) == 0


def test_network_delay_prefers_shorter_indirect_path():
    times = [[1, 2, 10], [1, 3, 1], [3, 2, 1]]
    assert network_delay_time(times, 3, 1) == 2


def test_network_delay_cycle_and_unreachable_node():
    times = [[1, 2, 1], [2, 1, 1]]
    assert network_delay_time(times, 3, 1) == -1
    assert network_delay_time(times, 2, 1) == 1


# ---------- ladder_length ----------
def test_ladder_examples():
    words = ["hot", "dot", "dog", "lot", "log", "cog"]
    assert ladder_length("hit", "cog", words) == 5
    assert ladder_length("hit", "cog", words[:-1]) == 0


def test_ladder_direct_and_missing():
    assert ladder_length("a", "c", ["a", "b", "c"]) == 2
    assert ladder_length("a", "c", []) == 0


def test_ladder_begin_not_in_list():
    assert ladder_length("hot", "dog", ["hot", "dog", "dot"]) == 3
    assert ladder_length("hit", "hot", ["hot"]) == 2


def test_ladder_shortest_not_first_found():
    words = ["si", "go", "se", "cm", "so", "ph", "mt", "db", "mb", "sb", "kr", "ln", "tm", "le", "av", "sm",
             "ar", "ci", "ca", "br", "ti", "ba", "to", "ra", "fa", "yo", "ow", "sn", "ya", "cr", "po", "fe",
             "ho", "ma", "re", "or", "rn", "au", "ur", "rh", "sr", "tc", "lt", "lo", "as", "fr", "nb", "yb",
             "if", "pb", "ge", "th", "pm", "rb", "sh", "co", "ga", "li", "ha", "hz", "no", "bi", "di", "hi",
             "qa", "pi", "os", "uh", "wm", "an", "me", "mo", "na", "la", "st", "er", "sc", "ne", "mn", "mi",
             "am", "ex", "pt", "io", "be", "fm", "ta", "tb", "ni", "mr", "pa", "he", "lr", "sq", "ye"]
    assert ladder_length("qa", "sq", words) == 5


# ---------- minimum_effort_path ----------
def test_effort_examples():
    assert minimum_effort_path([[1, 2, 2], [3, 8, 2], [5, 3, 5]]) == 2
    assert minimum_effort_path([[1, 2, 3], [3, 8, 4], [5, 3, 5]]) == 1


def test_effort_flat_and_single():
    big = [[1, 2, 1, 1, 1], [1, 2, 1, 2, 1], [1, 2, 1, 2, 1], [1, 2, 1, 2, 1], [1, 1, 1, 2, 1]]
    assert minimum_effort_path(big) == 0
    assert minimum_effort_path([[5]]) == 0


def test_effort_single_row_and_column():
    assert minimum_effort_path([[1, 10, 6, 7, 9, 10, 4, 9]]) == 9
    assert minimum_effort_path([[1], [5], [2]]) == 4


def test_effort_big_values():
    assert minimum_effort_path([[1, 10 ** 6], [1, 1]]) == 0


# ---------- swim_in_water ----------
def test_swim_examples():
    assert swim_in_water([[0, 2], [1, 3]]) == 3
    grid = [[0, 1, 2, 3, 4], [24, 23, 22, 21, 5], [12, 13, 14, 15, 16], [11, 17, 18, 19, 20], [10, 9, 8, 7, 6]]
    assert swim_in_water(grid) == 16


def test_swim_single():
    assert swim_in_water([[0]]) == 0


def test_swim_end_cell_is_bottleneck():
    assert swim_in_water([[0, 1], [2, 3]]) == 3
    assert swim_in_water([[3, 2], [0, 1]]) == 3  # must stand on start cell (elevation 3)


# ---------- cheapest_flights_within_k_stops ----------
def test_flights_examples():
    f = [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]]
    assert cheapest_flights_within_k_stops(4, f, 0, 3, 1) == 700
    g = [[0, 1, 100], [1, 2, 100], [0, 2, 500]]
    assert cheapest_flights_within_k_stops(3, g, 0, 2, 1) == 200
    assert cheapest_flights_within_k_stops(3, g, 0, 2, 0) == 500


def test_flights_unreachable_and_too_many_stops():
    g = [[0, 1, 1], [1, 2, 1], [2, 3, 1]]
    assert cheapest_flights_within_k_stops(4, g, 0, 3, 1) == -1
    assert cheapest_flights_within_k_stops(4, g, 0, 3, 2) == 3
    assert cheapest_flights_within_k_stops(4, g, 3, 0, 5) == -1


def test_flights_cheaper_path_uses_more_stops():
    g = [[0, 1, 1], [1, 2, 1], [2, 3, 1], [0, 3, 100]]
    assert cheapest_flights_within_k_stops(4, g, 0, 3, 0) == 100
    assert cheapest_flights_within_k_stops(4, g, 0, 3, 1) == 100
    assert cheapest_flights_within_k_stops(4, g, 0, 3, 2) == 3


def test_flights_dijkstra_trap():
    # cheapest overall (0->1->2->3->4 = 4) needs 3 stops; fewer stops cost more
    g = [[0, 1, 1], [1, 2, 1], [2, 3, 1], [3, 4, 1], [0, 2, 10], [2, 4, 10]]
    assert cheapest_flights_within_k_stops(5, g, 0, 4, 3) == 4
    assert cheapest_flights_within_k_stops(5, g, 0, 4, 2) == 12
    assert cheapest_flights_within_k_stops(5, g, 0, 4, 1) == 20


def test_flights_cycle():
    g = [[0, 1, 1], [1, 0, 1], [1, 2, 5]]
    assert cheapest_flights_within_k_stops(3, g, 0, 2, 3) == 6


# ---------- path_with_max_probability ----------
def test_prob_examples():
    e = [[0, 1], [1, 2], [0, 2]]
    assert path_with_max_probability(3, e, [0.5, 0.5, 0.2], 0, 2) == pytest.approx(0.25)
    assert path_with_max_probability(3, e, [0.5, 0.5, 0.3], 0, 2) == pytest.approx(0.3)


def test_prob_no_path():
    assert path_with_max_probability(3, [[0, 1]], [0.5], 0, 2) == 0.0


def test_prob_undirected_and_chain():
    assert path_with_max_probability(3, [[1, 0], [2, 1]], [0.5, 0.4], 0, 2) == pytest.approx(0.2)


def test_prob_certain_edges():
    assert path_with_max_probability(2, [[0, 1]], [1.0], 0, 1) == pytest.approx(1.0)


# ---------- minimum_obstacles_to_remove ----------
def test_obstacles_examples():
    assert minimum_obstacles_to_remove([[0, 1, 1], [1, 1, 0], [1, 1, 0]]) == 2
    assert minimum_obstacles_to_remove([[0, 1, 0, 0, 0], [0, 1, 0, 1, 0], [0, 0, 0, 1, 0]]) == 0


def test_obstacles_tiny():
    assert minimum_obstacles_to_remove([[0]]) == 0
    assert minimum_obstacles_to_remove([[0, 0]]) == 0
    assert minimum_obstacles_to_remove([[0], [1], [0]]) == 1


def test_obstacles_detour_is_cheaper_than_straight_line():
    grid = [[0, 1, 0, 0],
            [0, 0, 0, 1],
            [1, 1, 0, 0]]
    assert minimum_obstacles_to_remove(grid) == 0


def test_obstacles_full_wall():
    grid = [[0, 1, 0], [0, 1, 0], [0, 1, 0]]
    assert minimum_obstacles_to_remove(grid) == 1


# ---------- min_cost_valid_path ----------
def test_valid_path_examples():
    assert min_cost_valid_path([[1, 1, 1, 1], [2, 2, 2, 2], [1, 1, 1, 1], [2, 2, 2, 2]]) == 3
    assert min_cost_valid_path([[1, 1, 3], [3, 2, 2], [1, 1, 4]]) == 0
    assert min_cost_valid_path([[1, 2], [4, 3]]) == 1


def test_valid_path_small():
    assert min_cost_valid_path([[2, 2, 2], [2, 2, 2]]) == 3
    assert min_cost_valid_path([[4]]) == 0


def test_valid_path_single_row_column():
    assert min_cost_valid_path([[1, 1, 1]]) == 0
    assert min_cost_valid_path([[2, 2, 2]]) == 2
    assert min_cost_valid_path([[3], [3]]) == 0
    assert min_cost_valid_path([[4], [4]]) == 1


def test_valid_path_all_arrows_wrong_direction():
    assert min_cost_valid_path([[2, 2], [2, 2]]) == 2
