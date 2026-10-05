"""Solera error types."""


class SoleraError(Exception):
    """Base class for all Solera errors."""

    code = "invalid"


class WorkspaceLockTimeoutError(SoleraError):
    """The workspace's cross-process write lock could not be acquired in time."""

    code = "workspace_lock_timeout"


class FormatError(SoleraError):
    """A workspace file did not match its required format.

    Raised by the parsers in :mod:`solera.formats`. Solera fails fast on a
    malformed WorkItem / progress file rather than guessing intent.
    """

    code = "invalid_format"


class InvalidNameError(FormatError):
    """A caller supplied a name that is unsafe as one path component."""

    code = "invalid_name"


class OrderError(SoleraError):
    """Work-item order links are invalid or leave every open leaf blocked."""


class UnknownPredecessorError(OrderError):
    """An order link names a work item that does not exist."""

    code = "unknown_predecessor"


class OrderCycleError(OrderError):
    """Order links form a dependency cycle."""

    code = "order_cycle"


class OrderWaitsOnAncestorError(OrderError):
    """An item waits for an ancestor whose completion depends on that item."""

    code = "order_waits_on_ancestor"


class OrderWaitsOnDescendantError(OrderError):
    """An item waits for a descendant that cannot start before the item."""

    code = "order_waits_on_descendant"


class PlanningError(SoleraError):
    """A requested WorkItem edit would violate the planning tree."""


class UnknownWorkItemError(PlanningError):
    """A requested work-item identifier does not exist."""

    code = "unknown_work_item"


class UnknownParentError(PlanningError):
    """A requested parent identifier does not exist."""

    code = "unknown_parent"


class PlanningValueError(PlanningError, ValueError):
    """Invalid planning input, also catchable as ValueError for compatibility."""


class BlankGoalError(PlanningValueError):
    """A work-item goal is empty or whitespace-only."""

    code = "blank_goal"


class InvalidRealizesSlugError(PlanningValueError):
    """A realizes slug is empty or whitespace-only."""

    code = "invalid_realizes_slug"


class DuplicateRealizesSlugError(PlanningValueError):
    """A realizes list contains a duplicate slug."""

    code = "duplicate_realizes_slug"


class InvalidGateError(PlanningValueError):
    """A non-empty gate contains only whitespace."""

    code = "invalid_gate"


class InvalidOrderLinkError(PlanningValueError):
    """An order-link list has an invalid value or duplicate."""

    code = "invalid_order_link"


class InvalidAcceptError(PlanningValueError):
    """An acceptance mode does not fit the work item's shape."""

    code = "invalid_accept"


class AcceptRequiredError(PlanningValueError):
    """A new item without a gate omitted its acceptance mode."""

    code = "accept_required"


class AcceptLockedError(PlanningValueError):
    """An acceptance mode was changed after the editable statuses."""

    code = "accept_locked"


class InvalidPhaseError(PlanningValueError):
    """A progress phase was outside the supported values."""

    code = "invalid_phase"


class ItemProtectedError(PlanningError):
    """An agent tried to rewrite a result awaiting or holding person acceptance."""

    code = "item_protected"


class ParentIsLeafError(PlanningError):
    """A child was assigned to an item that already has a gate."""

    code = "parent_is_leaf"


class RootIndexNotSupportedError(PlanningError):
    """A root move supplied an index although roots have fixed ordering."""

    code = "root_index_not_supported"


class MoveUnderSelfError(PlanningError):
    """An item was moved under itself."""

    code = "move_under_self"


class MoveUnderDescendantError(PlanningError):
    """An item was moved under one of its descendants."""

    code = "move_under_descendant"


class ChildIndexOutOfRangeError(PlanningError):
    """A move supplied an invalid destination child index."""

    code = "index_out_of_range"


class MultipleParentsError(PlanningError):
    """A malformed tree gives one work item multiple parents."""

    code = "multiple_parents"


class GateError(SoleraError):
    """A gate could not be run at all (e.g. empty command, missing gate).

    Distinct from a gate that *ran and failed*: that is reported as a
    :class:`~solera.gate.GateResult` with ``passed=False``, not raised.
    """


class CheckError(SoleraError):
    """A person's check (or uncheck) of a work item was refused (D-2026-10-02-D)."""


class CheckContainerError(CheckError):
    """A container is done only when all of its children are done; it cannot be checked."""

    code = "check_container"


class CheckBlockedError(CheckError):
    """The item waits on order links or reaches no design node, so it cannot finish yet."""

    code = "check_blocked"


class CheckConflictError(CheckError):
    """The item changed while its gate ran outside the workspace lock; nothing was written."""

    code = "check_conflict"


class UncheckGatedError(CheckError):
    """A gate's verdict is not undone by hand; reopen gated work with repin."""

    code = "uncheck_gated"


class CheckCancelledError(CheckError):
    """A cancelled item is final and cannot be checked or unchecked."""

    code = "check_cancelled"


class JudgmentError(SoleraError):
    """A person-only judgment was refused by the work-item state machine."""


class NotPersonError(JudgmentError):
    """Accept or reject addressed an item not accepted by a person."""

    code = "not_person"


class BlankReasonError(JudgmentError):
    """A judgment that requires a reason received a blank one."""

    code = "blank_reason"


class NotInReviewError(JudgmentError):
    """Accept or reject addressed an item outside review."""

    code = "not_in_review"


class ReopenNotPersonError(JudgmentError):
    """Reopen addressed an item not accepted by a person."""

    code = "reopen_not_person"


class ReopenNotDoneError(JudgmentError):
    """Reopen addressed an item that is not done."""

    code = "reopen_not_done"


class CancelFinishedError(JudgmentError):
    """Cancel addressed an item already done or cancelled."""

    code = "cancel_finished"
