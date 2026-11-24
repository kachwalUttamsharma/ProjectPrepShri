"""Problem 06: extensible board-game engine (tic-tac-toe NxN + chess-lite).
Read lesson.md for the full spec.

Enums and exceptions are provided. Implement everything marked `...`
(and add the fields to the dataclasses).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class GameResult(Enum):
    IN_PROGRESS = "in_progress"
    WIN = "win"
    DRAW = "draw"


class GameError(Exception):
    """Base class for all game errors."""


class InvalidMoveError(GameError):
    """Rules reject the move (occupied, out of bounds, illegal for the piece...)."""


class OutOfTurnError(GameError):
    """move.player is not the current player."""


class GameOverError(GameError):
    """play() called after the game ended."""


class NothingToUndoError(GameError):
    """undo() with an empty history."""


# ------------------------------------------------------------------ value types
@dataclass(frozen=True, order=True)
class Position:
    """Fields: row: int, col: int. Ordered row-major (row, then col).
    offset(dr, dc) -> new Position shifted by (dr, dc)."""

    def offset(self, dr, dc):
        ...


@dataclass(frozen=True)
class Player:
    """Fields: name: str, symbol: str."""


@dataclass(frozen=True)
class Move:
    """Fields: player: Player, to: Position, frm: Position | None = None.
    `frm` is None for placement games (tic-tac-toe), required for piece games."""


class Board:
    """Board(rows, cols=None): cols defaults to rows. ValueError if either < 1.
    Attributes: rows, cols. Cells hold arbitrary objects (None = empty).

    in_bounds(pos) -> bool
    get(pos) -> cell or None          (ValueError if out of bounds)
    set(pos, item) -> None            (ValueError if out of bounds)
    remove(pos) -> removed item or None (ValueError if out of bounds)
    is_empty(pos) -> bool
    is_full() -> bool
    empty_positions() -> list[Position], row-major
    items() -> list[(Position, item)] for occupied cells, row-major
    """

    def __init__(self, rows, cols=None):
        ...

    def in_bounds(self, pos):
        ...

    def get(self, pos):
        ...

    def set(self, pos, item):
        ...

    def remove(self, pos):
        ...

    def is_empty(self, pos):
        ...

    def is_full(self):
        ...

    def empty_positions(self):
        ...

    def items(self):
        ...


# ------------------------------------------------------------------ engine
class GameRules(ABC):
    """Strategy: everything game-specific lives here; Game knows none of it.

    validate(board, move) -> None; raise InvalidMoveError if illegal.
    apply(board, move) -> captured item or None (mutates board).
    revert(board, move, captured) -> None (exactly undoes apply).
    evaluate(board, move) -> GameResult, called AFTER apply for the mover.
        WIN means the mover (move.player) won.
    All four are abstract.
    """

    @abstractmethod
    def validate(self, board, move):
        ...

    @abstractmethod
    def apply(self, board, move):
        ...

    @abstractmethod
    def revert(self, board, move, captured):
        ...

    @abstractmethod
    def evaluate(self, board, move):
        ...


class Game:
    """Game(board, players, rules). Attributes: board, players (list), rules.
    ValueError if fewer than 2 players or duplicate player symbols.

    Properties: current_player, result (GameResult), winner (Player | None),
    history (a NEW list of Move, oldest first).

    play(move) -> GameResult. Check order:
      1. result != IN_PROGRESS -> GameOverError
      2. move.player != current_player -> OutOfTurnError
      3. rules.validate (InvalidMoveError)
      4. rules.apply, record (move, captured), result = rules.evaluate
      5. WIN -> winner = move.player; IN_PROGRESS -> turn passes to the next
         player (round-robin); WIN/DRAW -> current_player stays the last mover.
    A rejected move changes nothing (board, turn, history).

    undo() -> the undone Move. NothingToUndoError if history empty. Reverts the
    board via rules.revert, makes the undone mover current again, result back
    to IN_PROGRESS, winner None.
    """

    def __init__(self, board, players, rules):
        ...

    @property
    def current_player(self):
        ...

    @property
    def result(self):
        ...

    @property
    def winner(self):
        ...

    @property
    def history(self):
        ...

    def play(self, move):
        ...

    def undo(self):
        ...


# ------------------------------------------------------------------ tic-tac-toe
class WinCondition(ABC):
    """Abstract: is_win(board, move) -> bool, called after the move is applied."""

    @abstractmethod
    def is_win(self, board, move):
        ...


class LineWinCondition(WinCondition):
    """LineWinCondition(length): True if, after `move`, there are >= `length`
    consecutive cells equal to move.player.symbol in a row, column or either
    diagonal THROUGH move.to. ValueError if length < 2.
    Only look at lines through the last move (O(length), not O(board))."""

    def __init__(self, length):
        ...

    def is_win(self, board, move):
        ...


class TicTacToeRules(GameRules):
    """TicTacToeRules(win_condition). Cells store the player's symbol (a str).

    validate: move.frm must be None, move.to in bounds and empty, else InvalidMoveError.
    apply: place symbol; return None.  revert: remove it.
    evaluate: win_condition.is_win -> WIN; elif board full -> DRAW; else IN_PROGRESS.
    A winning move that fills the board is a WIN, not a DRAW.
    """

    def __init__(self, win_condition):
        ...

    def validate(self, board, move):
        ...

    def apply(self, board, move):
        ...

    def revert(self, board, move, captured):
        ...

    def evaluate(self, board, move):
        ...


def tic_tac_toe(size=3, win_length=None, players=None):
    """Build a Game: Board(size), TicTacToeRules(LineWinCondition(win_length or size)).
    Default players: [Player("X", "X"), Player("O", "O")]."""
    ...


# ------------------------------------------------------------------ chess-lite
ORTHOGONAL = [(-1, 0), (1, 0), (0, -1), (0, 1)]
DIAGONAL = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
KNIGHT_JUMPS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
KING_STEPS = ORTHOGONAL + DIAGONAL


class MovementStrategy(ABC):
    """Abstract: targets(board, pos, owner) -> sorted list[Position] of squares a
    piece owned by `owner` standing on `pos` may move to: empty squares or squares
    holding an enemy piece (a board item whose .owner != owner). Never own pieces."""

    @abstractmethod
    def targets(self, board, pos, owner):
        ...


class SlidingMovement(MovementStrategy):
    """SlidingMovement(directions): from pos, walk each (dr, dc) until the edge;
    stop BEFORE an own piece, stop ON (include) an enemy piece."""

    def __init__(self, directions):
        ...

    def targets(self, board, pos, owner):
        ...


class StepMovement(MovementStrategy):
    """StepMovement(offsets): exactly one jump per (dr, dc); jumps ignore pieces
    in between. In bounds and not own-occupied."""

    def __init__(self, offsets):
        ...

    def targets(self, board, pos, owner):
        ...


class Piece(ABC):
    """Piece(owner, movement): owner is a Player.symbol str, movement a
    MovementStrategy. Attributes: owner, movement. Abstract property `kind` (str).

    legal_moves(board, pos) -> sorted list of Position (delegates to movement)
    can_move(board, frm, to) -> bool (to in legal_moves)
    """

    def __init__(self, owner, movement):
        ...

    @property
    @abstractmethod
    def kind(self):
        ...

    def legal_moves(self, board, pos):
        ...

    def can_move(self, board, frm, to):
        ...


class Rook(Piece):
    """Rook(owner): kind "rook"; SlidingMovement(ORTHOGONAL)."""


class Knight(Piece):
    """Knight(owner): kind "knight"; StepMovement(KNIGHT_JUMPS)."""


class King(Piece):
    """King(owner): kind "king"; StepMovement(KING_STEPS)."""


class ChessLiteRules(GameRules):
    """Cells store Piece objects. Move needs frm.

    validate -> InvalidMoveError unless: frm given, frm and to in bounds, a piece
      sits on frm, piece.owner == move.player.symbol, and piece.can_move(...).
    apply: remove any piece on `to` (the captured one, returned), move the piece.
    revert: move the piece back; put `captured` back on `to` if not None.
    evaluate: WIN if no enemy King remains on the board, else IN_PROGRESS.
      (No draws, check, castling or promotion; every position needs both kings.)
    """

    def validate(self, board, move):
        ...

    def apply(self, board, move):
        ...

    def revert(self, board, move, captured):
        ...

    def evaluate(self, board, move):
        ...


def chess_lite_game(pieces, size=8):
    """pieces: dict[Position, Piece]. Build a size x size Board, place them, and
    return Game(board, [Player("White", "W"), Player("Black", "B")], ChessLiteRules()).
    White moves first."""
    ...
