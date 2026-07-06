"""Direct-mode tests for the PactFactory intelligent contract.

Direct mode cannot exercise on-chain child deployment (gl.deploy_contract routes
through a no-op hook), so create_pact's deploy path is covered by integration tests.
Here we verify the deterministic surface: ownership, fee config, code upload, and
the authorization guard on the reputation callback.
"""

from conftest import hex_of

FEE_BPS = 200


def deploy_factory(direct_deploy, fee_bps=FEE_BPS):
    return direct_deploy("contracts/factory.py", fee_bps)


def test_construct_sets_owner_and_fee(direct_vm, direct_deploy, direct_owner):
    direct_vm.sender = direct_owner
    factory = deploy_factory(direct_deploy)
    assert factory.get_owner().lower() == hex_of(direct_owner)
    assert factory.get_fee_bps() == FEE_BPS
    assert factory.has_pact_code() is False
    assert factory.get_pact_count() == 0


def test_construct_rejects_bad_fee(direct_vm, direct_deploy):
    with direct_vm.expect_revert("fee_bps out of range"):
        deploy_factory(direct_deploy, fee_bps=20001)


def test_set_pact_code_owner_only(direct_vm, direct_deploy, direct_owner, direct_alice):
    direct_vm.sender = direct_owner
    factory = deploy_factory(direct_deploy)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("only the owner"):
        factory.set_pact_code(b"# some code")


def test_set_pact_code_success(direct_vm, direct_deploy, direct_owner):
    direct_vm.sender = direct_owner
    factory = deploy_factory(direct_deploy)
    factory.set_pact_code(b"# { \"Depends\": \"py-genlayer:x\" }\nclass Pact: ...")
    assert factory.has_pact_code() is True


def test_set_pact_code_rejects_empty(direct_vm, direct_deploy, direct_owner):
    direct_vm.sender = direct_owner
    factory = deploy_factory(direct_deploy)
    with direct_vm.expect_revert("must not be empty"):
        factory.set_pact_code(b"")


def test_set_fee_bps_owner_only(direct_vm, direct_deploy, direct_owner, direct_alice):
    direct_vm.sender = direct_owner
    factory = deploy_factory(direct_deploy)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("only the owner"):
        factory.set_fee_bps(300)


def test_set_fee_bps_success(direct_vm, direct_deploy, direct_owner):
    direct_vm.sender = direct_owner
    factory = deploy_factory(direct_deploy)
    factory.set_fee_bps(350)
    assert factory.get_fee_bps() == 350


def test_set_fee_bps_out_of_range(direct_vm, direct_deploy, direct_owner):
    direct_vm.sender = direct_owner
    factory = deploy_factory(direct_deploy)
    with direct_vm.expect_revert("fee_bps out of range"):
        factory.set_fee_bps(10001)


def test_create_pact_requires_code(direct_vm, direct_deploy, direct_owner, direct_bob):
    direct_vm.sender = direct_owner
    factory = deploy_factory(direct_deploy)
    with direct_vm.expect_revert("pact code not configured"):
        factory.create_pact(hex_of(direct_bob), "Do the thing", "criteria",
                             "2999-01-01T00:00:00Z")


def test_record_outcome_rejects_unregistered_caller(direct_vm, direct_deploy,
                                                    direct_owner, direct_alice):
    direct_vm.sender = direct_owner
    factory = deploy_factory(direct_deploy)
    # A random caller that was never deployed as a pact must be rejected.
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("not a registered pact"):
        factory.record_outcome(direct_alice, "kept")


def test_reputation_defaults_to_zero(direct_vm, direct_deploy, direct_owner, direct_alice):
    direct_vm.sender = direct_owner
    factory = deploy_factory(direct_deploy)
    rep = factory.get_reputation(hex_of(direct_alice))
    assert rep == {"kept": "0", "partial": "0", "broken": "0"}


def test_get_pacts_by_empty(direct_vm, direct_deploy, direct_owner, direct_alice):
    direct_vm.sender = direct_owner
    factory = deploy_factory(direct_deploy)
    assert factory.get_pacts_by(hex_of(direct_alice)) == []
