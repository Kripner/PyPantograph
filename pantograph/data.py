from typing import Optional, Tuple
from dataclasses import dataclass, field
from pantograph.expr import GoalState


@dataclass(frozen=True)
class MetavarDeclInfo:
    userName: str
    type: str
    depth: int
    kind: str
    numScopeArgs: int
    index: int

    @staticmethod
    def parse(payload: dict):
        return MetavarDeclInfo(
            userName=payload["userName"],
            type=payload["type"],
            depth=payload["depth"],
            kind=payload["kind"],
            numScopeArgs=payload["numScopeArgs"],
            index=payload["index"],
        )


@dataclass(frozen=True)
class MctxInfo:
    depth: int
    levelAssignDepth: int
    mvarCounter: int
    decls: dict[str, MetavarDeclInfo]
    userNames: dict[str, str]

    @staticmethod
    def parse(payload: dict):
        return MctxInfo(
            depth=payload["depth"],
            levelAssignDepth=payload["levelAssignDepth"],
            mvarCounter=payload["mvarCounter"],
            decls={k: MetavarDeclInfo.parse(v) for k, v in payload["decls"]},
            userNames=dict(payload["userNames"]),
        )

@dataclass(frozen=True)
class TacticInvocation:
    """
    One tactic invocation with the before/after goals extracted from Lean source
    code.
    """
    before: list[str]
    beforeIds: list[str]
    after: list[str]
    afterIds: list[str]
    tactic: str
    mctxBefore: MctxInfo
    mctxAfter: MctxInfo
    used_constants: list[str]

    @staticmethod
    def parse(payload: dict):
        return TacticInvocation(
            before=payload["goalBefore"].split("\n\n"),
            beforeIds=payload["goalBeforeIds"],
            after=payload["goalAfter"].split("\n\n"),
            afterIds=payload["goalAfterIds"],
            tactic=payload["tactic"],
            mctxBefore=MctxInfo.parse(payload["mctxBefore"]),
            mctxAfter=MctxInfo.parse(payload["mctxAfter"]),
            used_constants=payload.get('usedConstants', []),
        )

@dataclass(frozen=True)
class CompilationUnit:

    # Byte boundaries [begin, end[ of each compilation unit.
    i_begin: int
    i_end: int

    messages: list[str] = field(default_factory=list)

    invocations: Optional[list[TacticInvocation]] = None
    # If `goal_state` is none, maybe error has occurred. See `messages`
    goal_state: Optional[GoalState] = None
    goal_src_boundaries: Optional[list[Tuple[int, int]]] = None

    new_constants: Optional[list[str]] = None

    @staticmethod
    def parse(payload: dict, goal_state_sentinel=None):
        i_begin = payload["boundary"][0]
        i_end = payload["boundary"][1]
        messages = payload["messages"]

        if (invocation_payload := payload.get("invocations")) is not None:
            invocations = [
                TacticInvocation.parse(i) for i in invocation_payload
            ]
        else:
            invocations = None

        if (state_id := payload.get("goalStateId")) is not None:
            goal_state = GoalState.parse_inner(int(state_id), payload["goals"], goal_state_sentinel)
            goal_src_boundaries = payload["goalSrcBoundaries"]
        else:
            goal_state = None
            goal_src_boundaries = None

        new_constants = payload.get("newConstants")

        return CompilationUnit(
            i_begin,
            i_end,
            messages,
            invocations,
            goal_state,
            goal_src_boundaries,
            new_constants
        )
