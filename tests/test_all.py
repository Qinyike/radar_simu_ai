"""
单元测试 - 全模块覆盖

覆盖：
1. 契约验证 (SimResult, ProcessedResult)
2. LFMCW 端到端
3. MIMO TDMA 端到端
4. PMCW 端到端
5. 窗函数工具
6. 注册表
7. 公共工具 (noise, axes)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from contracts import SimResult, ProcessedResult


passed = 0
failed = 0


def run_test(name, func):
    global passed, failed
    print(f"测试 {passed + failed + 1}: {name}...", end=" ")
    try:
        func()
        print("✓")
        passed += 1
    except Exception as e:
        print(f"✗ {e}")
        failed += 1


# ============================================================
# 1. 契约
# ============================================================
def test_sim_result():
    bb = np.zeros((1, 128, 256), dtype=np.complex128)
    sr = SimResult(name="t", baseband=bb, fc=77e9, bandwidth=150e6,
                   fs=20e6, prf=20e3, num_chirps=128, samples_per_chirp=256)
    assert sr.name == "t"
    assert sr.baseband.shape == (1, 128, 256)


def test_processed_result():
    rd = np.zeros((100, 64))
    pr = ProcessedResult(name="t", range_profile=np.zeros(100),
                         range_doppler=rd,
                         range_axis=np.arange(100) * 1.0,
                         doppler_axis=np.linspace(-5, 5, 64))
    assert pr.range_doppler.shape == (100, 64)


# ============================================================
# 2. LFMCW
# ============================================================
def test_lfmcw_e2e():
    from simulators import get_simulator
    from processors import get_processor
    sim = get_simulator("lfmcw")
    targets = [{"range": 50.0, "velocity": 3.0, "rcs": 15}]
    sr = sim.simulate(targets=targets, snr_db=30.0, seed=42)
    assert sr.name == "lfmcw"
    proc = get_processor("lfmcw")
    pr = proc(sr)
    assert pr.range_doppler.ndim == 2
    idx = np.unravel_index(np.argmax(pr.range_doppler), pr.range_doppler.shape)
    det_range = pr.range_axis[idx[0]]
    assert abs(det_range - 50.0) < 2.0


# ============================================================
# 3. MIMO TDMA
# ============================================================
def test_mimo_tdma_e2e():
    import numpy as np
    from simulators.mimo_simulator import MimoLfmcwSimulator, MimoAntennaArray
    from processors.mimo_processor import process_mimo, mimo_dbf_angle_estimation

    arr = MimoAntennaArray(num_tx=4, num_rx=4, fc=77e9)
    sim = MimoLfmcwSimulator(antenna_array=arr, waveform_mode='tdma',
                             fc=77e9, bandwidth=150e6, chirp_duration=40e-6,
                             fs=20e6, prf=20e3, num_chirps_per_frame=128)
    targets = [{"range": 50.0, "velocity": 1.5, "angle": np.radians(5), "rcs": 10}]
    sr = sim.simulate(targets, snr_db=25.0, seed=42)
    assert sr.baseband.shape[0] == 4  # 4 RX
    assert sr.baseband.shape[1] == 512  # 128 * 4 TX

    pr = process_mimo(sr)
    assert pr.range_doppler.ndim == 2

    dbf = mimo_dbf_angle_estimation(pr)
    assert 'angle_spectrum' in dbf
    assert len(dbf['detected_angles']) > 0


# ============================================================
# 4. PMCW
# ============================================================
def test_pmcw_e2e():
    from simulators.pmcw_simulator import PmcwSimulator
    from processors.pmcw_processor import process_pmcw

    sim = PmcwSimulator(fc=77e9, chip_rate=50e6, code_type='barker',
                        code_length=13, pri=50e-6, num_pulses=64)
    targets = [{"range": 15.0, "velocity": 2.0, "rcs": 10}]
    sr = sim.simulate(targets, snr_db=25.0, seed=42)
    assert sr.name == "pmcw"
    assert sr.baseband.shape == (1, 64, 13)

    pr = process_pmcw(sr)
    assert pr.range_doppler.ndim == 2
    idx = np.unravel_index(np.argmax(pr.range_doppler), pr.range_doppler.shape)
    det_range = pr.range_axis[idx[0]]
    assert abs(det_range - 15.0) < 4.0


# ============================================================
# 5. 窗函数
# ============================================================
def test_window_utils():
    from processors.window_utils import get_window
    for name in ['hamming', 'hanning', 'blackman', 'taylor', 'kaiser', 'none']:
        w = get_window(name, 256)
        assert len(w) == 256, f"{name} 长度错误"
        assert not np.any(np.isnan(w)), f"{name} 包含 NaN"
    try:
        get_window('invalid', 128)
        assert False, "应抛出 ValueError"
    except ValueError:
        pass


# ============================================================
# 6. 注册表
# ============================================================
def test_simulator_registry():
    from simulators import get_simulator, SIMULATOR_REGISTRY
    assert "lfmcw" in SIMULATOR_REGISTRY
    assert "pmcw" in SIMULATOR_REGISTRY
    assert "mimo_tdma" in SIMULATOR_REGISTRY
    sim = get_simulator("lfmcw")
    assert hasattr(sim, 'simulate')
    try:
        get_simulator("nonexistent")
        assert False
    except ValueError:
        pass


def test_processor_registry():
    from processors import get_processor, PROCESSOR_REGISTRY
    assert "lfmcw" in PROCESSOR_REGISTRY
    assert "pmcw" in PROCESSOR_REGISTRY
    proc = get_processor("lfmcw")
    assert callable(proc)
    try:
        get_processor("nonexistent")
        assert False
    except ValueError:
        pass


# ============================================================
# 7. 工具函数
# ============================================================
def test_add_awgn():
    from utils.noise import add_awgn
    sig = np.ones((1, 10, 20), dtype=np.complex128)
    noisy = add_awgn(sig, 20.0)
    assert noisy.shape == sig.shape
    assert not np.allclose(sig, noisy)


def test_compute_axes():
    from utils.axes import compute_range_axis, compute_doppler_axis, compute_edges
    ra = compute_range_axis(150e6, 800, 3e8)
    assert len(ra) == 400
    assert abs(ra[1] - ra[0] - 1.0) < 0.01  # 1m resolution

    da = compute_doppler_axis(20e3, 256, 77e9)
    assert len(da) == 256

    edges = compute_edges(np.arange(10))
    assert len(edges) == 11


# ============================================================
# 运行
# ============================================================
if __name__ == "__main__":
    print("=" * 70)
    print("全模块测试套件")
    print("=" * 70)

    run_test("SimResult 契约", test_sim_result)
    run_test("ProcessedResult 契约", test_processed_result)
    run_test("LFMCW 端到端", test_lfmcw_e2e)
    run_test("MIMO TDMA 端到端", test_mimo_tdma_e2e)
    run_test("PMCW 端到端", test_pmcw_e2e)
    run_test("窗函数工具", test_window_utils)
    run_test("仿真器注册表", test_simulator_registry)
    run_test("处理器注册表", test_processor_registry)
    run_test("add_awgn", test_add_awgn)
    run_test("坐标轴工具", test_compute_axes)

    print("\n" + "=" * 70)
    if failed == 0:
        print(f"✓ 全部 {passed} 项测试通过！")
    else:
        print(f"✗ {failed} 项失败, {passed} 项通过")
    print("=" * 70)
    sys.exit(0 if failed == 0 else 1)
