# stdlib
from typing import Any

# third party
import numpy as np

# syft absolute
import syft as sy
from syft.core.adp.data_subject_ledger import DataSubjectLedger
from syft.core.adp.data_subject_ledger import convert_constants_to_indices
from syft.core.adp.ledger_store import DictLedgerStore


class UserBudget:
    def __init__(self, value: int) -> None:
        self.budget = value
        self.current_spend = 0


user_budget = UserBudget(150)


def get_budget_for_user(*args: Any, **kwargs: Any) -> int:
    return user_budget.budget


def deduct_epsilon_for_user(
    verify_key: Any, old_budget: int, epsilon_spend: int
) -> None:
    user_budget.budget = old_budget - epsilon_spend
    user_budget.current_spend = epsilon_spend


def test_privacy_budget_spend_on_publish():
    fred_nums = np.array([25, 35, 21])
    sally_nums = np.array([8, 11, 10])

    fred_tensor = sy.Tensor(fred_nums).annotate_with_dp_metadata(
        lower_bound=0, upper_bound=122, data_subject="fred"
    )

    sally_tensor = sy.Tensor(sally_nums).annotate_with_dp_metadata(
        lower_bound=0, upper_bound=122, data_subject="sally"
    )

    result = fred_tensor + sally_tensor

    ledger_store = DictLedgerStore()

    user_key = b"1231"

    ledger = DataSubjectLedger.get_or_create(store=ledger_store, user_key=user_key)

    pub_result_sally = sally_tensor.publish(
        get_budget_for_user=get_budget_for_user,
        deduct_epsilon_for_user=deduct_epsilon_for_user,
        ledger=ledger,
        sigma=50,
        private=True,
    )

    assert pub_result_sally is not None

    eps_spend_for_sally = user_budget.current_spend

    pub_result_fred = sally_tensor.publish(
        get_budget_for_user=get_budget_for_user,
        deduct_epsilon_for_user=deduct_epsilon_for_user,
        ledger=ledger,
        sigma=50,
        private=True,
    )

    assert pub_result_fred is not None

    eps_spend_for_fred = user_budget.current_spend

    # Epsilon spend for sally should be equal to fred
    # since they impact the same of values in the data independently
    assert eps_spend_for_sally == eps_spend_for_fred

    pub_result_comb = result.publish(
        get_budget_for_user=get_budget_for_user,
        deduct_epsilon_for_user=deduct_epsilon_for_user,
        ledger=ledger,
        sigma=50,
        private=True,
    )

    assert pub_result_comb is not None

    # TODO: Need to confirm if this ratio will always be less than 1
    # assert (eps_spend_for_fred + eps_spend_for_sally) / combined_eps_spend < 1

    # This should only filter out values of fred or sally
    pub_result_comb2 = result.publish(
        get_budget_for_user=get_budget_for_user,
        deduct_epsilon_for_user=deduct_epsilon_for_user,
        ledger=ledger,
        sigma=50,
        private=True,
    )
    assert pub_result_comb2 is not None
    # assert user_budget.current_spend == 0.0
    # TODO: Do we need caching?

    mul_tensor = (fred_tensor + sally_tensor) * 2

    print(mul_tensor.child.lipschitz_bound)
    # This should only filter out values of fred or sally
    pub_result_comb4 = mul_tensor.publish(
        get_budget_for_user=get_budget_for_user,
        deduct_epsilon_for_user=deduct_epsilon_for_user,
        ledger=ledger,
        sigma=50,
        private=True,
    )
    assert pub_result_comb4 is not None


def test_publish_new_subjects() -> None:
    """Test that publishing works when data of new data subjects are published, i.e. ledger expands, PB unchanged if
    new data subjects have the same epsilon, etc"""
    pass


def test_publish_existing_subjects() -> None:
    """Test the ledger is updated correctly when existing data subjects have more data published"""
    pass
