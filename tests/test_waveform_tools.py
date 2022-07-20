import numpy as np
import pytest
from matplotlib import pyplot as plt
from scipy.signal.windows import gaussian, blackman

from qualang_tools.config import (
    drag_gaussian_pulse_waveforms,
    drag_cosine_pulse_waveforms,
)
from qualang_tools.config.waveform_tools import (
    flattop_gaussian_waveform,
    flattop_cosine_waveform,
    flattop_tanh_waveform,
    flattop_blackman_waveform,
    blackman_integral_waveform,
)


@pytest.mark.parametrize("length", [16, 21, 60])
def test_drag_no_drag_gaussian_to_scipy(length):
    amp = 0.1
    sigma = length // 5
    I_wf, Q_wf = drag_gaussian_pulse_waveforms(
        amplitude=amp,
        length=length,
        sigma=sigma,
        alpha=0,
        delta=0,
        detuning=0,
        subtracted=False,
    )
    I_sub_wf, Q_sub_wf = drag_gaussian_pulse_waveforms(
        amplitude=amp,
        length=length,
        sigma=sigma,
        alpha=0,
        delta=0,
        detuning=0,
        subtracted=True,
    )
    gauss = amp * gaussian(length, sigma)
    sub_gauss = gauss - gauss[0]
    assert (I_wf == gauss).all()
    assert (I_sub_wf == sub_gauss).all()


@pytest.mark.parametrize("length", [16, 21, 60])
def test_drag_no_detune_symmetric(length):
    amp = 0.1
    sigma = length // 5
    I_gauss_wf, Q_gauss_wf = drag_gaussian_pulse_waveforms(
        amplitude=amp,
        length=length,
        sigma=sigma,
        alpha=0.1,
        delta=10e6,
        detuning=0,
        subtracted=False,
    )
    I_cos_wf, Q_cos_wf = drag_cosine_pulse_waveforms(
        amplitude=amp, length=length, alpha=0.1, delta=10e6, detuning=0
    )

    I_gauss_first_half = I_gauss_wf[: length // 2]
    Q_gauss_first_half = Q_gauss_wf[: length // 2]
    if length % 2 == 0:
        I_gauss_second_half = I_gauss_wf[length // 2 :]
        Q_gauss_second_half = Q_gauss_wf[length // 2 :]
    else:
        I_gauss_second_half = I_gauss_wf[length // 2 + 1 :]
        Q_gauss_second_half = Q_gauss_wf[length // 2 + 1 :]

    I_cos_first_half = I_cos_wf[: length // 2]
    Q_cos_first_half = Q_cos_wf[: length // 2]
    if length % 2 == 0:
        I_cos_second_half = I_cos_wf[length // 2 :]
        Q_cos_second_half = Q_cos_wf[length // 2 :]
    else:
        I_cos_second_half = I_cos_wf[length // 2 + 1 :]
        Q_cos_second_half = Q_cos_wf[length // 2 + 1 :]

    assert (np.array(I_gauss_first_half) == np.flip(I_gauss_second_half)).all()
    assert (np.array(Q_gauss_first_half) == -np.flip(Q_gauss_second_half)).all()
    np.testing.assert_allclose(
        I_cos_first_half, np.flip(I_cos_second_half), rtol=1e-7, atol=1e-7
    )
    np.testing.assert_allclose(
        Q_cos_first_half, -np.flip(Q_cos_second_half), rtol=1e-7, atol=1e-7
    )


def test_drag_detune():
    amp = 0.1
    length = 60
    sigma = length // 5
    I_gauss_wf, Q_gauss_wf = drag_gaussian_pulse_waveforms(
        amplitude=amp,
        length=length,
        sigma=sigma,
        alpha=0.1,
        delta=10e6,
        detuning=1e6,
        subtracted=True,
    )
    I_cos_wf, Q_cos_wf = drag_cosine_pulse_waveforms(
        amplitude=amp, length=length, alpha=0.1, delta=10e6, detuning=1e6
    )
    # plt.figure()
    # plt.plot(I_gauss_wf); plt.plot(Q_gauss_wf);
    # plt.figure()
    # plt.plot(I_cos_wf); plt.plot(Q_cos_wf);
    # fmt: off
    I_cos_wf_saved = [0.0, 0.00018757672355762065, 0.0007492062480890956, 0.001681587624964176, 0.002979222690258811, 0.004634421599986756, 0.006637311388457736, 0.008975848335524833, 0.011635835120196633, 0.014600943905999777, 0.0178527466431549, 0.02137075398014205, 0.02513246424921537, 0.02911342402414721, 0.033287301741886516, 0.03762597583158239, 0.04209963870397941, 0.04667691782174653, 0.0513250148978447, 0.05600986405633606, 0.06069630954061614, 0.06534830327116405, 0.06992912224249428, 0.07440160541163188, 0.07872840937326084, 0.08287228174535365, 0.08679635080962321, 0.09046442956992089, 0.09384133201533117, 0.096893199009905, 0.09958783088447047, 0.101895023484411, 0.10378690413716896, 0.1052382637506687, 0.10622688104461486, 0.10673383475595741, 0.10674379955238371, 0.10624532133747262, 0.10523106764134782, 0.10369804886369208, 0.10164780627334541, 0.09908656287100143, 0.09602533348837639, 0.0924799908273187, 0.08847128453334618, 0.08402481084676613, 0.07917093087663929, 0.07394463609327032, 0.06838536022768293, 0.06253673739491354, 0.056446306914480576, 0.0501651659779772, 0.04374757200181161, 0.03725049719368061, 0.03073313854511192, 0.024256387129911346, 0.01788226123008625, 0.011673308417393868, 0.005691982280900334, 1.2711786904350342e-17]
    I_gauss_wf_saved = [0.0, 0.0008875225425574015, 0.0018983754635498663, 0.0030430713499851273, 0.004332191648683379, 0.005776314887541078, 0.007385940055475904, 0.009171398035789518, 0.011142741166172226, 0.013309598530790084, 0.01568098288868166, 0.018265034637604215, 0.02106868930248254, 0.024097258037070156, 0.027353915710633482, 0.03083909830260132, 0.03454982030375858, 0.03847893313373392, 0.04261435650401514, 0.046938325254019676, 0.05142670339802799, 0.05604842382963707, 0.06076511528733483, 0.06553097692044282, 0.07029295453485387, 0.07499126116024635, 0.07956026823983828, 0.08392977325714038, 0.08802662619633855, 0.09177667248249059, 0.0951069458270477, 0.09794802268306707, 0.10023643269181937, 0.10191700822449404, 0.10294505211635449, 0.10328820663142062, 0.10292791862434655, 0.10186041516528348, 0.10009712932758374, 0.0976645456534733, 0.09460346688786558, 0.09096773560171412, 0.08682247402933431, 0.08224193075062194, 0.07730704207917433, 0.0721028280111641, 0.06671574678678907, 0.06123112857577537, 0.0557307981641859, 0.050290979932079594, 0.04498055738181544, 0.039859735737301276, 0.03497913148031824, 0.030379288828603974, 0.026090601582286623, 0.022133600646662942, 0.018519553681506207, 0.015251314135083127, 0.012324352418582657, 0.009727901851784893]
    Q_cos_wf_saved = [0.0, 0.015229154236153808, 0.030294620956736032, 0.04503453306858582, 0.059290643794334304, 0.07291008574246628, 0.08574706932653135, 0.09766450139934081, 0.10853550587993034, 0.11824482927102077, 0.12669011527969734, 0.13378303424882854, 0.13945025476404838, 0.14363424660176285, 0.14629390610677914, 0.1474049971115724, 0.14696040260952087, 0.14497018454741545, 0.14146145128335058, 0.13647803443960382, 0.13007997904117713, 0.12234285294446784, 0.1133568836027886, 0.10322593216277297, 0.09206631671580952, 0.08000549822066916, 0.06718064414818153, 0.0537370862587855, 0.03982669009369308, 0.025606154727155214, 0.011235262080173251, -0.003124904373259761, -0.017313751373328322, -0.031172957908682148, -0.044548227470372126, -0.05729099086547082, -0.06926004054158573, -0.08032307820072043, -0.0903581585141806, -0.09925501297701138, -0.10691623934615062, -0.11325834367439264, -0.11821262366387045, -0.12172588389794964, -0.12376097544767974, -0.1242971543656559, -0.12333025565282922, -0.12087268138843409, -0.11695320382543199, -0.11161658634937424, -0.10492302725329297, -0.0969474332716386, -0.08777853171972343, -0.07751783188002564, -0.06627844794280555, -0.054183797327140695, -0.04136618956279317, -0.027965322088381112, -0.014126700304377508, -3.270520286556616e-17]
    Q_gauss_wf_saved = [0.02685223105361867, 0.031735854412607456, 0.03721449053394794, 0.04329081197460029, 0.04995009768922662, 0.057157254514725656, 0.06485416791726922, 0.07295758624366663, 0.08135774963344587, 0.0899179686688894, 0.09847533684420468, 0.10684272398237203, 0.11481214491046478, 0.12215953042448256, 0.12865084863105328, 0.13404943830107574, 0.13812432724876883, 0.14065922417167326, 0.1414617985056694, 0.14037280622753434, 0.13727458606859477, 0.1320984449273739, 0.12483047625384801, 0.11551541151227541, 0.1042581907892966, 0.09122305003152946, 0.07663005285522212, 0.0607491361167256, 0.043891880982542056, 0.02640135512271865, 0.008640487238880598, -0.00902047605023885, -0.026216825497031807, -0.042601933260798946, -0.0578588830882541, -0.07171064199099994, -0.08392831941995403, -0.09433717644704917, -0.10282018122136355, -0.10931904831726906, -0.1138328386654816, -0.11641432427414825, -0.1171644299397772, -0.11622514653618164, -0.11377136343526954, -0.11000208975736377, -0.10513152642816648, -0.09938041648736923, -0.09296804447910577, -0.08610518293579005, -0.07898820139876205, -0.07179446756587363, -0.06467908698579124, -0.05777295229614541, -0.05118200920651258, -0.04498759680243263, -0.03924768548716097, -0.03399881692434198, -0.02925854557260732, -0.025028188870131272]
    # fmt: on
    np.testing.assert_allclose(I_gauss_wf, I_gauss_wf_saved)
    np.testing.assert_allclose(Q_gauss_wf, Q_gauss_wf_saved)
    np.testing.assert_allclose(I_cos_wf, I_cos_wf_saved)
    np.testing.assert_allclose(Q_cos_wf, Q_cos_wf_saved)


def test_drag_zero_delta():
    with pytest.raises(
        Exception,
        match="Cannot create a DRAG pulse",
    ):
        drag_gaussian_pulse_waveforms(
            amplitude=0.1,
            length=40,
            sigma=8,
            alpha=0.1,
            delta=0,
            detuning=0,
            subtracted=False,
        )
    with pytest.raises(
        Exception,
        match="Cannot create a DRAG pulse",
    ):
        drag_cosine_pulse_waveforms(
            amplitude=0.1, length=40, alpha=0.1, delta=0, detuning=0
        )


@pytest.mark.parametrize(
    "flat_length, rise_fall_length",
    list(zip([0, 16, 16, 21, 21, 60, 60], [8, 5, 10, 5, 10, 0, 10])),
)
def test_flattop_flat_length(flat_length, rise_fall_length):
    amp = 0.1

    flattop_gaussian = flattop_gaussian_waveform(amp, flat_length, rise_fall_length)
    flattop_cosine = flattop_cosine_waveform(amp, flat_length, rise_fall_length)
    flattop_tanh = flattop_tanh_waveform(amp, flat_length, rise_fall_length)
    flattop_blackman = flattop_blackman_waveform(amp, flat_length, rise_fall_length)
    flattop_gaussian_rise = flattop_gaussian_waveform(
        amp, flat_length, rise_fall_length, return_part="rise"
    )
    flattop_cosine_rise = flattop_cosine_waveform(
        amp, flat_length, rise_fall_length, return_part="rise"
    )
    flattop_tanh_rise = flattop_tanh_waveform(
        amp, flat_length, rise_fall_length, return_part="rise"
    )
    flattop_blackman_rise = flattop_blackman_waveform(
        amp, flat_length, rise_fall_length, return_part="rise"
    )
    flattop_gaussian_fall = flattop_gaussian_waveform(
        amp, flat_length, rise_fall_length, return_part="fall"
    )
    flattop_cosine_fall = flattop_cosine_waveform(
        amp, flat_length, rise_fall_length, return_part="fall"
    )
    flattop_tanh_fall = flattop_tanh_waveform(
        amp, flat_length, rise_fall_length, return_part="fall"
    )
    flattop_blackman_fall = flattop_blackman_waveform(
        amp, flat_length, rise_fall_length, return_part="fall"
    )

    assert np.allclose(
        flattop_gaussian,
        flattop_gaussian_rise + [amp] * flat_length + flattop_gaussian_fall,
        rtol=1e-10,
    )
    assert np.allclose(
        flattop_cosine,
        flattop_cosine_rise + [amp] * flat_length + flattop_cosine_fall,
        rtol=1e-10,
    )
    assert np.allclose(
        flattop_tanh,
        flattop_tanh_rise + [amp] * flat_length + flattop_tanh_fall,
        rtol=1e-10,
    )
    assert np.allclose(
        flattop_blackman,
        flattop_blackman_rise + [amp] * flat_length + flattop_blackman_fall,
        rtol=1e-10,
    )

    assert np.allclose(
        flattop_gaussian_rise + flattop_gaussian_fall,
        (amp * gaussian(2 * rise_fall_length, rise_fall_length / 5)).tolist(),
        rtol=1e-10,
    )
    cosine_rise_part = (
        amp * 0.5 * (1 - np.cos(np.linspace(0, np.pi, rise_fall_length)))
    ).tolist()
    assert np.allclose(
        flattop_cosine_rise + flattop_cosine_fall,
        cosine_rise_part + cosine_rise_part[::-1],
        rtol=1e-10,
    )
    tanh_rise_part = (
        amp * 0.5 * (1 + np.tanh(np.linspace(-4, 4, rise_fall_length)))
    ).tolist()
    assert np.allclose(
        flattop_tanh_rise + flattop_tanh_fall,
        tanh_rise_part + tanh_rise_part[::-1],
        rtol=1e-10,
    )
    assert np.allclose(
        flattop_blackman_rise + flattop_blackman_fall,
        (amp * blackman(2 * rise_fall_length)).tolist(),
        rtol=1e-10,
    )


@pytest.mark.parametrize(
    "pulse_length, v_start, v_end",
    list(
        zip(
            np.linspace(2, 31, 30).astype(int).tolist() + [10],
            np.linspace(0, 0.5, 30).tolist() + [-0.2],
            np.linspace(0.5, 0, 30).tolist() + [-0.2],
        )
    ),
)
def test_blackman_integral_waveform(pulse_length, v_start, v_end):
    waveform = blackman_integral_waveform(pulse_length, v_start, v_end)
    assert len(waveform) == pulse_length
    assert np.isclose(waveform[0], v_start, rtol=1e-10)
    assert np.isclose(waveform[-1], v_end, rtol=1e-10)
