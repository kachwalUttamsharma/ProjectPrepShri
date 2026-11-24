import dataclasses

import pytest

from exercises import *

P = Position


def mv(game, r, c, who=None):
    p = game.players[who] if who is not None else game.current_player
    return Move(p, P(r, c))


def play_all(game, cells):
    res = None
    for r, c in cells:
        res = game.play(mv(game, r, c))
    return res


# ---- value types and board
def test_position_is_frozen_ordered_dataclass():
    assert P(1, 2) == P(1, 2) and hash(P(1, 2)) == hash(P(1, 2))
    assert P(0, 5) < P(1, 0)
    assert P(1, 1).offset(-1, 2) == P(0, 3)
    with pytest.raises(dataclasses.FrozenInstanceError):
        P(0, 0).row = 3


def test_player_and_move_are_frozen_dataclasses():
    a = Player("Ann", "A")
    m = Move(a, P(0, 0))
    assert m.frm is None and m.to == P(0, 0) and m.player == a
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.to = P(1, 1)
    assert Move(a, P(1, 1), P(0, 0)).frm == P(0, 0)


def test_board_basic_ops():
    b = Board(2, 3)
    assert (b.rows, b.cols) == (2, 3)
    assert Board(4).cols == 4
    assert b.in_bounds(P(1, 2)) and not b.in_bounds(P(2, 0)) and not b.in_bounds(P(0, -1))
    assert b.get(P(0, 0)) is None and b.is_empty(P(0, 0))
    b.set(P(0, 1), "x")
    assert b.get(P(0, 1)) == "x" and not b.is_empty(P(0, 1))
    assert b.remove(P(0, 1)) == "x"
    assert b.remove(P(0, 1)) is None


def test_board_out_of_bounds_raises_value_error():
    b = Board(3)
    for call in (lambda: b.get(P(3, 0)), lambda: b.set(P(-1, 0), "x"), lambda: b.remove(P(0, 9))):
        with pytest.raises(ValueError):
            call()
    with pytest.raises(ValueError):
        Board(0)


def test_board_full_empty_and_items_row_major():
    b = Board(2)
    assert b.empty_positions() == [P(0, 0), P(0, 1), P(1, 0), P(1, 1)]
    b.set(P(1, 0), "a")
    b.set(P(0, 1), "b")
    assert b.items() == [(P(0, 1), "b"), (P(1, 0), "a")]
    assert b.empty_positions() == [P(0, 0), P(1, 1)]
    assert not b.is_full()
    b.set(P(0, 0), "c")
    b.set(P(1, 1), "d")
    assert b.is_full()


# ---- abstractions
def test_abstract_classes_cannot_be_instantiated():
    for cls in (GameRules, WinCondition, MovementStrategy, Piece):
        with pytest.raises(TypeError):
            cls()


def test_error_hierarchy():
    for e in (InvalidMoveError, OutOfTurnError, GameOverError, NothingToUndoError):
        assert issubclass(e, GameError)


# ---- game constructor
def test_game_requires_two_distinct_players():
    rules = TicTacToeRules(LineWinCondition(3))
    with pytest.raises(ValueError):
        Game(Board(3), [Player("a", "X")], rules)
    with pytest.raises(ValueError):
        Game(Board(3), [Player("a", "X"), Player("b", "X")], rules)


def test_tic_tac_toe_factory_defaults():
    g = tic_tac_toe()
    assert g.board.rows == 3 and g.board.cols == 3
    assert [p.symbol for p in g.players] == ["X", "O"]
    assert g.current_player == g.players[0]
    assert g.result is GameResult.IN_PROGRESS and g.winner is None and g.history == []


# ---- tic-tac-toe play
def test_turns_alternate_and_board_updates():
    g = tic_tac_toe()
    assert g.play(mv(g, 0, 0)) is GameResult.IN_PROGRESS
    assert g.board.get(P(0, 0)) == "X"
    assert g.current_player == g.players[1]
    g.play(mv(g, 1, 1))
    assert g.board.get(P(1, 1)) == "O"
    assert g.current_player == g.players[0]


def test_out_of_turn_rejected_without_side_effects():
    g = tic_tac_toe()
    with pytest.raises(OutOfTurnError):
        g.play(Move(g.players[1], P(0, 0)))
    assert g.board.is_empty(P(0, 0)) and g.current_player == g.players[0]


def test_invalid_moves_do_not_change_state_or_turn():
    g = tic_tac_toe()
    g.play(mv(g, 0, 0))
    with pytest.raises(InvalidMoveError):
        g.play(mv(g, 0, 0))  # occupied
    with pytest.raises(InvalidMoveError):
        g.play(mv(g, 3, 3))  # out of bounds
    with pytest.raises(InvalidMoveError):
        g.play(Move(g.players[1], P(1, 1), P(0, 0)))  # frm not allowed
    assert g.current_player == g.players[1]
    assert len(g.history) == 1


def test_row_win():
    g = tic_tac_toe()
    res = play_all(g, [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)])
    assert res is GameResult.WIN and g.result is GameResult.WIN
    assert g.winner == g.players[0]


def test_column_win_second_player():
    g = tic_tac_toe()
    res = play_all(g, [(0, 0), (0, 1), (1, 0), (1, 1), (2, 2), (2, 1)])
    assert res is GameResult.WIN and g.winner == g.players[1]


def test_diagonal_and_anti_diagonal_win():
    g = tic_tac_toe()
    assert play_all(g, [(0, 0), (0, 1), (1, 1), (0, 2), (2, 2)]) is GameResult.WIN
    g = tic_tac_toe()
    assert play_all(g, [(0, 2), (0, 0), (1, 1), (0, 1), (2, 0)]) is GameResult.WIN


def test_win_on_middle_cell_of_line():
    g = tic_tac_toe()
    # X fills ends of row 0 first, wins by placing the middle last
    assert play_all(g, [(0, 0), (1, 0), (0, 2), (1, 1), (0, 1)]) is GameResult.WIN


def test_draw():
    g = tic_tac_toe()
    # X O X / X O O / O X X  -> no line
    cells = [(0, 0), (0, 1), (0, 2), (1, 1), (1, 0), (1, 2), (2, 1), (2, 0), (2, 2)]
    assert play_all(g, cells[:-1]) is GameResult.IN_PROGRESS
    assert g.play(mv(g, *cells[-1])) is GameResult.DRAW
    assert g.winner is None


def test_win_on_last_cell_beats_draw():
    # final move fills the board AND completes a line -> WIN, not DRAW
    # X O X / O X O / O X X  -> X diagonal 00,11,22
    g2 = tic_tac_toe()
    seq = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (2, 0), (2, 2)]
    res = play_all(g2, seq)
    assert res is GameResult.WIN and g2.board.is_full()
    assert g2.winner == g2.players[0]


def test_play_after_game_over_raises():
    g = tic_tac_toe()
    play_all(g, [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)])
    with pytest.raises(GameOverError):
        g.play(mv(g, 2, 2, who=1))
    assert g.board.is_empty(P(2, 2))


def test_history_is_a_copy_in_order():
    g = tic_tac_toe()
    g.play(mv(g, 0, 0))
    g.play(mv(g, 1, 1))
    h = g.history
    assert [m.to for m in h] == [P(0, 0), P(1, 1)]
    h.clear()
    assert len(g.history) == 2


# ---- configurable board / win length
def test_connect_k_on_larger_board():
    g = tic_tac_toe(size=5, win_length=4)
    assert play_all(g, [(0, 0), (4, 0), (0, 1), (4, 1), (0, 2), (4, 2)]) is GameResult.IN_PROGRESS
    assert g.play(mv(g, 0, 3)) is GameResult.WIN


def test_three_in_row_not_enough_when_k_is_four():
    g = tic_tac_toe(size=4, win_length=4)
    play_all(g, [(0, 0), (3, 0), (0, 1), (3, 1), (0, 2)])
    assert g.result is GameResult.IN_PROGRESS


def test_diagonal_win_on_5x5_k4_not_from_corner():
    g = tic_tac_toe(size=5, win_length=4)
    # X on (1,1),(2,2),(3,3),(4,4); O wastes moves in row 0
    res = play_all(g, [(1, 1), (0, 0), (2, 2), (0, 1), (3, 3), (0, 3), (4, 4)])
    assert res is GameResult.WIN


def test_three_player_game_rotates():
    ps = [Player("a", "A"), Player("b", "B"), Player("c", "C")]
    g = tic_tac_toe(size=4, win_length=3, players=ps)
    g.play(Move(ps[0], P(0, 0)))
    g.play(Move(ps[1], P(1, 0)))
    assert g.current_player == ps[2]
    g.play(Move(ps[2], P(2, 0)))
    assert g.current_player == ps[0]


def test_custom_win_condition_is_pluggable():
    class Never(WinCondition):
        def is_win(self, board, move):
            return False

    g = Game(Board(2), [Player("a", "A"), Player("b", "B")], TicTacToeRules(Never()))
    res = play_all(g, [(0, 0), (0, 1), (1, 0), (1, 1)])
    assert res is GameResult.DRAW


def test_line_win_condition_validates_length():
    with pytest.raises(ValueError):
        LineWinCondition(1)


# ---- undo
def test_undo_restores_board_and_turn():
    g = tic_tac_toe()
    g.play(mv(g, 0, 0))
    g.play(mv(g, 1, 1))
    m = g.undo()
    assert m.to == P(1, 1) and g.board.is_empty(P(1, 1))
    assert g.current_player == g.players[1]
    assert len(g.history) == 1


def test_undo_after_win_reopens_game():
    g = tic_tac_toe()
    play_all(g, [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)])
    g.undo()
    assert g.result is GameResult.IN_PROGRESS and g.winner is None
    assert g.current_player == g.players[0]
    assert g.play(mv(g, 2, 2)) is GameResult.IN_PROGRESS


def test_undo_with_no_history():
    with pytest.raises(NothingToUndoError):
        tic_tac_toe().undo()


# ---- chess-lite: movement strategies and pieces
def test_piece_attributes():
    r = Rook("W")
    assert r.owner == "W" and r.kind == "rook"
    assert Knight("B").kind == "knight" and King("B").kind == "king"
    assert isinstance(r, Piece)


def test_rook_slides_and_stops_at_blockers():
    b = Board(5)
    r = Rook("W")
    b.set(P(2, 2), r)
    b.set(P(2, 4), Knight("B"))  # enemy: capturable, stop
    b.set(P(0, 2), King("W"))   # friend: blocked before it
    assert r.legal_moves(b, P(2, 2)) == sorted(
        [P(1, 2), P(3, 2), P(4, 2), P(2, 0), P(2, 1), P(2, 3), P(2, 4)]
    )
    assert r.can_move(b, P(2, 2), P(2, 4))
    assert not r.can_move(b, P(2, 2), P(0, 2))
    assert not r.can_move(b, P(2, 2), P(3, 3))


def test_knight_jumps_over_pieces_and_respects_edges():
    b = Board(8)
    n = Knight("W")
    b.set(P(0, 0), n)
    b.set(P(1, 0), Rook("B"))  # adjacent blockers are irrelevant
    b.set(P(2, 1), Rook("W"))  # own piece on a target square
    assert n.legal_moves(b, P(0, 0)) == [P(1, 2)]


def test_knight_center_has_eight_moves():
    b = Board(8)
    n = Knight("W")
    b.set(P(4, 4), n)
    assert len(n.legal_moves(b, P(4, 4))) == 8


def test_king_one_step_any_direction():
    b = Board(8)
    k = King("W")
    b.set(P(0, 0), k)
    assert k.legal_moves(b, P(0, 0)) == [P(0, 1), P(1, 0), P(1, 1)]
    b.set(P(1, 1), Rook("B"))
    assert P(1, 1) in k.legal_moves(b, P(0, 0))
    b.set(P(0, 1), Rook("W"))
    assert P(0, 1) not in k.legal_moves(b, P(0, 0))


def test_movement_strategies_are_reusable_building_blocks():
    b = Board(5)

    class Bishop(Piece):
        kind = "bishop"

        def __init__(self, owner):
            super().__init__(owner, SlidingMovement(DIAGONAL))

    bish = Bishop("W")
    b.set(P(0, 0), bish)
    assert bish.legal_moves(b, P(0, 0)) == [P(i, i) for i in range(1, 5)]
    assert StepMovement(ORTHOGONAL).targets(b, P(0, 0), "W") == [P(0, 1), P(1, 0)]


# ---- chess-lite game
def kings(extra=None):
    d = {P(0, 0): King("W"), P(7, 7): King("B")}
    d.update(extra or {})
    return d


def test_chess_lite_setup_and_turn_order():
    g = chess_lite_game(kings())
    assert [p.symbol for p in g.players] == ["W", "B"]
    assert g.current_player.symbol == "W"
    assert g.board.rows == 8 and g.board.get(P(0, 0)).kind == "king"


def test_chess_lite_legal_move_updates_board():
    g = chess_lite_game(kings({P(3, 3): Rook("W")}))
    w, b = g.players
    assert g.play(Move(w, P(3, 6), P(3, 3))) is GameResult.IN_PROGRESS
    assert g.board.get(P(3, 3)) is None and g.board.get(P(3, 6)).kind == "rook"
    assert g.current_player == b


def test_chess_lite_rejects_bad_moves():
    g = chess_lite_game(kings({P(3, 3): Rook("W"), P(5, 5): Knight("B")}))
    w = g.players[0]
    bad = [
        Move(w, P(3, 4)),                 # no source
        Move(w, P(4, 4), P(3, 3)),        # rook can't go diagonal
        Move(w, P(6, 6), P(5, 5)),        # not your piece
        Move(w, P(2, 2), P(4, 4)),        # empty source
        Move(w, P(9, 9), P(3, 3)),        # out of bounds target
        Move(w, P(3, 3), P(9, 9)),        # out of bounds source
        Move(w, P(0, 0), P(0, 0)),        # king onto itself
    ]
    for m in bad:
        with pytest.raises(InvalidMoveError):
            g.play(m)
    assert g.current_player == w and g.history == []


def test_chess_lite_blocked_path_rejected():
    g = chess_lite_game(kings({P(3, 0): Rook("W"), P(3, 2): Knight("W")}))
    with pytest.raises(InvalidMoveError):
        g.play(Move(g.players[0], P(3, 5), P(3, 0)))


def test_chess_lite_capture_and_undo_restores_captured_piece():
    g = chess_lite_game(kings({P(3, 3): Rook("W"), P(3, 6): Knight("B")}))
    w, b = g.players
    target = g.board.get(P(3, 6))
    g.play(Move(w, P(3, 6), P(3, 3)))
    assert g.board.get(P(3, 6)).kind == "rook"
    g.undo()
    assert g.board.get(P(3, 6)) is target
    assert g.board.get(P(3, 3)).kind == "rook"
    assert g.current_player == w


def test_chess_lite_capturing_king_wins():
    g = chess_lite_game(kings({P(7, 0): Rook("W")}))
    w, b = g.players
    g.play(Move(w, P(6, 0), P(7, 0)))        # rook steps up, no capture
    assert g.result is GameResult.IN_PROGRESS
    g.play(Move(b, P(6, 7), P(7, 7)))        # black king steps aside
    res = g.play(Move(w, P(6, 7), P(6, 0)))  # rook captures the king along row 6
    assert res is GameResult.WIN and g.winner == w
    with pytest.raises(GameOverError):
        g.play(Move(b, P(5, 7), P(6, 7)))


def test_chess_lite_undo_win_reopens():
    g = chess_lite_game({P(0, 0): King("W"), P(0, 5): King("B"), P(0, 3): Rook("W")})
    w = g.players[0]
    assert g.play(Move(w, P(0, 5), P(0, 3))) is GameResult.WIN
    g.undo()
    assert g.result is GameResult.IN_PROGRESS and g.winner is None
    assert g.board.get(P(0, 5)).kind == "king" and g.board.get(P(0, 5)).owner == "B"


def test_engine_is_game_agnostic():
    # same Game class drives both rule sets
    assert type(tic_tac_toe()) is type(chess_lite_game(kings()))
