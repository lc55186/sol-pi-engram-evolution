"""
BOSS-AI-R 合规引擎测试

覆盖场景：
1. 录音前合规检查
2. 同意管理
3. 三重录音指示
4. 数据保留策略
5. 权利响应
6. PIPIA 报告
7. 情绪识别权限
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.compliance import (
    ComplianceEngine,
    ConsentType,
    RecordingIndicator,
    RightsRequest,
    RightsRequestType,
)


class TestComplianceEngine:
    """合规引擎测试类"""

    def setup_method(self):
        self.engine = ComplianceEngine()
        self.user_id = "test-user-001"
        self.tenant_id = "test-tenant-001"

    def test_check_recording_permission_no_agreement(self):
        """未签署协议 → 拒绝录音"""
        result = self.engine.check_recording_permission(
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            scene="business_negotiation"
        )

        assert result["allowed"] is False
        assert "用户协议" in result["reason"]

    def test_check_recording_permission_with_agreement(self):
        """已签署协议 + 所有同意 → 允许录音"""
        # 添加所有必要同意
        self.engine.add_consent(self.user_id, ConsentType.USER_AGREEMENT, self.tenant_id)
        self.engine.add_consent(self.user_id, ConsentType.MICROPHONE, self.tenant_id)
        self.engine.add_consent(self.user_id, ConsentType.CLOUD_UPLOAD, self.tenant_id)
        self.engine.add_consent(self.user_id, ConsentType.PRIVACY_POLICY, self.tenant_id)

        result = self.engine.check_recording_permission(
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            scene="business_negotiation"
        )

        assert result["allowed"] is True

    def test_check_recording_permission_private_scene(self):
        """私密场景 → 强烈提示告知模式"""
        self.engine.add_consent(self.user_id, ConsentType.USER_AGREEMENT, self.tenant_id)
        self.engine.add_consent(self.user_id, ConsentType.MICROPHONE, self.tenant_id)
        self.engine.add_consent(self.user_id, ConsentType.CLOUD_UPLOAD, self.tenant_id)
        self.engine.add_consent(self.user_id, ConsentType.PRIVACY_POLICY, self.tenant_id)

        result = self.engine.check_recording_permission(
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            scene="private"
        )

        assert result["allowed"] is True
        assert any("私密场景" in r for r in result["requirements"])

    def test_third_party_recording_denied(self):
        """有非参与方 → 谨慎拒绝"""
        self.engine.add_consent(self.user_id, ConsentType.USER_AGREEMENT, self.tenant_id)
        self.engine.add_consent(self.user_id, ConsentType.MICROPHONE, self.tenant_id)
        self.engine.add_consent(self.user_id, ConsentType.CLOUD_UPLOAD, self.tenant_id)
        self.engine.add_consent(self.user_id, ConsentType.PRIVACY_POLICY, self.tenant_id)

        result = self.engine.check_recording_permission(
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            scene="business_negotiation",
            has_third_party=True
        )

        assert result["allowed"] is False

    def test_activate_recording_indicators(self):
        """激活三重录音指示"""
        session_id = "test-session-001"

        # Android
        indicators = self.engine.activate_recording_indicators(session_id, "android")
        assert RecordingIndicator.APP_PULSE in indicators
        assert RecordingIndicator.SYSTEM_ANDROID in indicators
        assert RecordingIndicator.NOTIFICATION in indicators

        # iOS
        indicators = self.engine.activate_recording_indicators(session_id, "ios")
        assert RecordingIndicator.APP_PULSE in indicators
        assert RecordingIndicator.SYSTEM_IOS in indicators
        assert RecordingIndicator.NOTIFICATION not in indicators

    def test_handle_data_subject_deletion(self):
        """被录音方删除请求"""
        request = RightsRequest(
            request_type=RightsRequestType.DELETION,
            requester_id="speaker-001",
            tenant_id=self.tenant_id,
            speaker_id="opponent_main"
        )

        result = self.engine.handle_data_subject_request(request)

        assert result.status == "completed"
        assert "删除" in result.result

    def test_enforce_retention_policy(self):
        """数据保留策略执行"""
        result = self.engine.enforce_retention_policy(
            tenant_id=self.tenant_id,
            session_ids=["s1", "s2", "s3"]
        )

        assert "deleted" in result
        assert "retained" in result
        assert result["policy_days"] == 90

    def test_emotion_permission_denied_by_default(self):
        """情绪识别默认关闭"""
        allowed = self.engine.check_emotion_permission(self.user_id, self.tenant_id)
        assert allowed is False

    def test_emotion_permission_after_consent(self):
        """用户开启情绪识别后允许"""
        self.engine.add_consent(self.user_id, ConsentType.EMOTION_ANALYSIS, self.tenant_id)

        allowed = self.engine.check_emotion_permission(self.user_id, self.tenant_id)
        assert allowed is True

    def test_generate_pipia_report(self):
        """生成 PIPIA 报告"""
        report = self.engine.generate_pipia_report(self.tenant_id)

        assert report.tenant_id == self.tenant_id
        assert len(report.chapters) == 4
        assert "声纹处理" in report.chapters
        assert "情绪识别" in report.chapters
        assert "云数据处理" in report.chapters
        assert "数据出境" in report.chapters
        assert report.status == "completed"

    def test_cleanup_session_voiceprint_destroyed(self):
        """会话清理后声纹销毁"""
        session_id = "test-session-cleanup"
        
        # 激活指示
        self.engine.activate_recording_indicators(session_id, "android")
        assert session_id in self.engine._indicators
        
        # 清理（方法名为 cleanup_session_data）
        result = self.engine.cleanup_session_data(session_id, self.tenant_id)
        
        assert result["voiceprint_destroyed"] is True
        assert result["vectors_deleted"] is True
        assert session_id not in self.engine._indicators

    def test_compliance_summary(self):
        """合规摘要"""
        summary = self.engine.get_compliance_summary(self.tenant_id)

        assert summary["pipia_completed"] is True
        assert summary["rights_response_days"] == 15
        assert summary["triple_indicator"] is True
        assert summary["forbidden_features"]["third_party_recording"] is False
        assert summary["forbidden_features"]["lie_detection"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
