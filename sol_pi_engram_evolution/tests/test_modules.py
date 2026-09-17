"""
BOSS-AI-R 音频流水线 + 计费模块 联合测试
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.billing import SubscriptionManager, SubscriptionTier
from modules.realtime_audio import AudioLevel, AudioPipeline


def test_audio_pipeline():
    """音频流水线测试"""
    ap = AudioPipeline()

    # 1. 创建会话
    session = ap.create_session('tenant-001', 'user-001')
    assert session.session_id is not None
    assert session.tenant_id == 'tenant-001'
    print(f'[✓] 会话创建: {session.session_id[:8]}')

    # 2. 开始录音
    result = ap.start_recording(session.session_id)
    assert result is True
    status = ap.get_session_status(session.session_id)
    assert status['is_recording'] is True
    print(f'[✓] 开始录音: recording={status["is_recording"]}')

    # 3. 处理音频帧（模拟）
    # 生成模拟 PCM 数据（1s 正弦波）
    import math
    sample_rate = 16000
    freq = 440
    duration_ms = 1000
    num_samples = int(sample_rate * duration_ms / 1000)

    samples = []
    for i in range(num_samples):
        val = int(16000 * math.sin(2 * math.pi * freq * i / sample_rate))
        samples.append(struct.pack('<h', val))

    pcm_data = b''.join(samples)

    # 处理帧
    result = ap.process_frame(session.session_id, pcm_data)
    print(f'[✓] 音频帧处理: {"有结果" if result else "无结果（V0.1 模拟）"}')

    # 4. 网络状态更新
    ap.update_network_status(session.session_id, rtt_ms=100, packet_loss=0.01, snr_db=25)
    status = ap.get_session_status(session.session_id)
    assert status['network_rtt_ms'] == 100
    print(f'[✓] 网络状态更新: rtt={status["network_rtt_ms"]}ms, level={status["current_level"]}')

    # 5. 弱网降级
    ap.update_network_status(session.session_id, rtt_ms=600, packet_loss=0.08, snr_db=8)
    status = ap.get_session_status(session.session_id)
    assert status['current_level'] == AudioLevel.L_B_WEAK_NETWORK.value
    print(f'[✓] 弱网降级: level={status["current_level"]}')

    # 6. 停止录音
    stats = ap.stop_recording(session.session_id)
    assert stats['total_frames'] > 0
    print(f'[✓] 停止录音: frames={stats["total_frames"]}, chunks={stats["total_chunks"]}')

    # 7. 清理
    ap.cleanup_session(session.session_id)
    status = ap.get_session_status(session.session_id)
    assert status == {}
    print('[✓] 会话清理完成')


def test_billing():
    """计费模块测试"""
    sm = SubscriptionManager()

    # 1. 创建 L2 订阅
    sub = sm.create_subscription('tenant-001', 'user-001', SubscriptionTier.L2_PROFESSIONAL, 12800)
    assert sub.tier == SubscriptionTier.L2_PROFESSIONAL
    assert sub.price_rmb == 12800
    print(f'[✓] L2 订阅创建: tier={sub.tier.value}, price={sub.price_rmb}')

    # 2. 检查功能权限
    access = sm.check_access('tenant-001', 'user-001', 'whisper')
    assert access['allowed'] is True
    print(f'[✓] 权限检查: whisper={access["allowed"]}')

    access_emotion = sm.check_access('tenant-001', 'user-001', 'emotion')
    assert access_emotion['allowed'] is True
    print(f'[✓] 权限检查: emotion={access_emotion["allowed"]}')

    # 3. 记录使用量
    sm.record_usage('tenant-001', 'session-001', 3600, asr_cost=3.5, llm_cost=0.5)
    sm.record_usage('tenant-001', 'session-002', 1800, asr_cost=1.75, llm_cost=0.25)
    quota = sm.get_quota_summary('tenant-001')
    assert quota['used_minutes'] == 90.0  # 3600+1800=5400s=90min
    print(f'[✓] 使用量记录: used={quota["used_minutes"]}min, sessions={quota.get("used_sessions", 2)}')

    # 4. 成本计算
    cost = sm.get_monthly_cost('tenant-001')
    assert cost.total_cost > 0
    assert cost.savings > 0  # 自建方案更便宜
    print(f'[✓] 成本计算: total={cost.total_cost:.2f}元, self_hosted={cost.self_hosted_cost:.2f}元, savings={cost.savings:.2f}元')

    # 5. 自建切换判断
    should_switch = sm.should_switch_to_self_hosted(600, 50)
    assert should_switch is True
    print(f'[✓] 自建切换: users=600 → switch={should_switch}')

    should_not_switch = sm.should_switch_to_self_hosted(100, 50)
    assert should_not_switch is False
    print(f'[✓] 自建切换: users=100 → switch={should_not_switch}')

    # 6. L0 免费用户
    sm.create_subscription('tenant-l0', 'user-l0', SubscriptionTier.L0_FREE)
    access_l0 = sm.check_access('tenant-l0', 'user-l0', 'whisper')
    assert access_l0['allowed'] is False
    assert access_l0['upgrade_to'] == 'L2'
    print(f'[✓] L0 权限: whisper={access_l0["allowed"]}, upgrade_to={access_l0["upgrade_to"]}')

    # 7. L1 基础用户
    sm.create_subscription('tenant-l1', 'user-l1', SubscriptionTier.L1_BASIC, 1980)
    access_l1 = sm.check_access('tenant-l1', 'user-l1', 'whisper')
    assert access_l1['allowed'] is False
    access_post = sm.check_access('tenant-l1', 'user-l1', 'post_session')
    assert access_post['allowed'] is True
    print(f'[✓] L1 权限: whisper={access_l1["allowed"]}, post_session={access_post["allowed"]}')


if __name__ == '__main__':
    print('=== 音频流水线测试 ===')
    test_audio_pipeline()
    print()
    print('=== 计费模块测试 ===')
    test_billing()
    print()
    print('=== 所有测试通过 ===')
