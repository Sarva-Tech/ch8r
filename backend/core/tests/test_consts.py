import pytest
import core.consts as consts


class TestDashboardUserIdPrefix:
    @pytest.mark.unit
    def test_dashboard_user_id_prefix_value(self):
        """DASHBOARD_USER_ID_PREFIX constant equals 'dashboard'"""
        assert consts.DASHBOARD_USER_ID_PREFIX == "dashboard"

    @pytest.mark.unit
    def test_registered_user_id_prefix_does_not_exist(self):
        """REGISTERED_USER_ID_PREFIX no longer exists in consts"""
        assert not hasattr(consts, "REGISTERED_USER_ID_PREFIX")
