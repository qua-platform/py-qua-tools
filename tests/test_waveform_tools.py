import numpy as np
import pytest
from matplotlib import pyplot as plt
from scipy.signal.windows import gaussian, blackman

from qualang_tools.config import (
    drag_gaussian_pulse_waveforms,
    drag_cosine_pulse_waveforms,
)
from qualang_tools.config.waveform_tools import flattop_gaussian_waveform, flattop_cosine_waveform, \
    flattop_tanh_waveform, flattop_blackman_waveform, blackman_integral_waveform


@pytest.mark.parametrize("length", [16, 21, 60])
def test_drag_no_drag_gaussian_to_scipy(length):
    amp = 0.1
    sigma = length // 5
    I_wf, Q_wf = drag_gaussian_pulse_waveforms(
        amplitude=amp,
        length=length,
        sigma=sigma,
        alpha=0,
        delta=10e6,
        detuning=0,
        subtracted=False,
    )
    I_sub_wf, Q_sub_wf = drag_gaussian_pulse_waveforms(
        amplitude=amp,
        length=length,
        sigma=sigma,
        alpha=0,
        delta=10e6,
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
    I_cos_wf_saved = [0.0, 0.00024374148853632675, 0.0009725881600901635, 0.0021794295035906636, 0.0038524906872997857, 0.005975445831626842, 0.00852757508380137, 0.01148396400397284, 0.014815743370347783, 0.01849036712663068, 0.022471925831890092, 0.02672149263442166, 0.031197498480396872, 0.035856132987992326, 0.0406517671709289, 0.04553739398425602, 0.0504650824918043, 0.05538644132067452, 0.06025308697474198, 0.0650171125273732, 0.06963155220393452, 0.07405083739738985, 0.07823123973511752, 0.08213129693141474, 0.08571221731700719, 0.08893825913286912, 0.09177708090904897, 0.09420005951789301, 0.09618257279264741, 0.09770424393415389, 0.09874914528721458, 0.0993059594508967, 0.09936809609005531, 0.09893376323494824, 0.09800599228810611, 0.09659261639857673, 0.0947062023091586, 0.0923639362280906, 0.08958746471866336, 0.08640269203417901, 0.08283953574746804, 0.07893164292974487, 0.07471606951903556, 0.07023292588001014, 0.06552499189126637, 0.06063730519965241, 0.05561672655106642, 0.0505114863406133, 0.04537071671965065, 0.040243973751080464, 0.03518075421559119, 0.030230011739152258, 0.02543967693506602, 0.020856186231848806, 0.01652402399112713, 0.012485282408028708, 0.008779243531052782, 0.005441987540396365, 0.002506031184876374, 5.2497062597879414e-18]
    I_gauss_wf_saved = [0.0, 0.0010045521229354861, 0.002172691409540741, 0.0035213394561623987, 0.0050672109464589676, 0.006826358377534424, 0.008813654287846211, 0.011042218284695387, 0.013522799639661562, 0.016263129812785833, 0.019267262834323104, 0.022534924845637745, 0.026060897086520093, 0.029834459007655287, 0.03383891976932858, 0.03805126694848613, 0.042441960619253996, 0.046974898930937654, 0.051607577764093256, 0.056291461946709614, 0.06097257888869704, 0.0655923374707242, 0.0700885658370291, 0.07439675173544955, 0.0784514586706859, 0.08218788092729502, 0.08554349107939795, 0.08845972556499608, 0.0908836478791712, 0.09276952548338402, 0.0940802560751665, 0.09478858169192231, 0.09487803531579983, 0.09434357406430467, 0.09319186532578669, 0.09144120674575609, 0.08912107701895511, 0.08627133108600091, 0.08294106959095746, 0.07918722734414498, 0.07507293814234665, 0.07066574285908024, 0.06603571366645232, 0.0612535692691146, 0.056388854070545565, 0.05150824847166743, 0.04667406848766008, 0.04194300123128338, 0.03736510936760612, 0.03298312329300984, 0.028832025437042726, 0.024938917577161976, 0.02132315012483893, 0.01799668255638399, 0.014964636902488216, 0.012226001655244586, 0.009774441584013645, 0.00759916958213438, 0.005685839464524327, 0.004017423170336556]
    Q_cos_wf_saved = [0.0, 0.006290371893716454, 0.01251938892040738, 0.01862632922160565, 0.024551730382033416, 0.03023800278516544, 0.035630023521434136, 0.04067570468425146, 0.045326530156958526, 0.049538055323391755, 0.05327036452249644, 0.05648848150923576, 0.05916272867527408, 0.06126903131838117, 0.06278916382356141, 0.06371093522551495, 0.06402831225479415, 0.06374147862227054, 0.06285682996141188, 0.06138690451839536, 0.05935025034920752, 0.056771230443579686, 0.053679767840948835, 0.05011103342685937, 0.04610507969280684, 0.04170642430225867, 0.03696358782463058, 0.03192859047194485, 0.026656413094839827, 0.021204428061166767, 0.015631805947824182, 0.009998904221590034, 0.004366644265026483, -0.0012041167827517296, -0.006653212854636346, -0.011921787959670426, -0.016952900958855186, -0.021692109865220733, -0.026088029642250665, -0.03009285775877207, -0.033662862101901884, -0.036758826248874235, -0.0393464475492838, -0.041396683966654114, -0.042886046166983, -0.04379683191631166, -0.04411730045332862, -0.04384178513017571, -0.04297074325836053, -0.04151074275023235, -0.03947438580298834, -0.036880170524773825, -0.03375229204431085, -0.03012038526995065, -0.026019212064607902, -0.02148829617348857, -0.01657150977597486, -0.011316616025991998, -0.005774772391611559, -1.3506575393600958e-17]
    Q_gauss_wf_saved = [0.01108941854612205, 0.01311026331429008, 0.015386270211303886, 0.017920906019150272, 0.02071076700458421, 0.02374432888923591, 0.027000814569505628, 0.03044926168886572, 0.03404787575174195, 0.03774375294895139, 0.04147304942555189, 0.04516165988981962, 0.0487264482064222, 0.05207704642582644, 0.05511820762069671, 0.057752663521527865, 0.05988440234610834, 0.061422247846149323, 0.06228359009468663, 0.062398094547272305, 0.06171120082846798, 0.06018721845271839, 0.05781183453403661, 0.054593868872534486, 0.05056614407774654, 0.04578538107678551, 0.04033108103175882, 0.034303410175886936, 0.02782016067115726, 0.02101291436096115, 0.014022583399089454, 0.006994538757341837, 7.356183389317997e-05, -0.006601135963937771, -0.012900586372957254, -0.018710211204838147, -0.023933257576833882, -0.02849338003698411, -0.03233627954877567, -0.03543036423149765, -0.037766451380869516, -0.039356580948225535, -0.040232054143529934, -0.040440844666632184, -0.04004455264859985, -0.03911508202540621, -0.037731221018227894, -0.03597529373722884, -0.03393003041185075, -0.03167577660641126, -0.029288130482786386, -0.02683606423043458, -0.024380553537552595, -0.021973709433940405, -0.019658381557885823, -0.017468181938027905, -0.015427864266756026, -0.01355398541530546, -0.011855773223260143, -0.010336126680798696]
    # fmt: on
    np.testing.assert_allclose(I_gauss_wf, I_gauss_wf_saved)
    np.testing.assert_allclose(Q_gauss_wf, Q_gauss_wf_saved)
    np.testing.assert_allclose(I_cos_wf, I_cos_wf_saved)
    np.testing.assert_allclose(Q_cos_wf, Q_cos_wf_saved)


@pytest.mark.parametrize("flat_length, rise_fall_length", list(zip([0, 16, 16, 21, 21, 60, 60], [8, 5, 10, 5, 10, 0, 10])))
def test_flattop_flat_length(flat_length, rise_fall_length):
    amp = 0.1

    flattop_gaussian = flattop_gaussian_waveform(amp, flat_length, rise_fall_length)
    flattop_cosine = flattop_cosine_waveform(amp, flat_length, rise_fall_length)
    flattop_tanh = flattop_tanh_waveform(amp, flat_length, rise_fall_length)
    flattop_blackman = flattop_blackman_waveform(amp, flat_length, rise_fall_length)
    flattop_gaussian_rise = flattop_gaussian_waveform(amp, flat_length, rise_fall_length, return_part="rise")
    flattop_cosine_rise = flattop_cosine_waveform(amp, flat_length, rise_fall_length, return_part="rise")
    flattop_tanh_rise = flattop_tanh_waveform(amp, flat_length, rise_fall_length, return_part="rise")
    flattop_blackman_rise = flattop_blackman_waveform(amp, flat_length, rise_fall_length, return_part="rise")
    flattop_gaussian_fall = flattop_gaussian_waveform(amp, flat_length, rise_fall_length, return_part="fall")
    flattop_cosine_fall = flattop_cosine_waveform(amp, flat_length, rise_fall_length, return_part="fall")
    flattop_tanh_fall = flattop_tanh_waveform(amp, flat_length, rise_fall_length, return_part="fall")
    flattop_blackman_fall = flattop_blackman_waveform(amp, flat_length, rise_fall_length, return_part="fall")

    assert np.allclose(flattop_gaussian, flattop_gaussian_rise + [amp] * flat_length + flattop_gaussian_fall, rtol=1e-10)
    assert np.allclose(flattop_cosine, flattop_cosine_rise + [amp] * flat_length + flattop_cosine_fall, rtol=1e-10)
    assert np.allclose(flattop_tanh, flattop_tanh_rise + [amp] * flat_length + flattop_tanh_fall, rtol=1e-10)
    assert np.allclose(flattop_blackman, flattop_blackman_rise + [amp] * flat_length + flattop_blackman_fall, rtol=1e-10)

    assert np.allclose(flattop_gaussian_rise + flattop_gaussian_fall, (amp * gaussian(2 * rise_fall_length, rise_fall_length / 5)).tolist(), rtol=1e-10)
    cosine_rise_part = (amp * 0.5 * (1 - np.cos(np.linspace(0, np.pi, rise_fall_length)))).tolist()
    assert np.allclose(flattop_cosine_rise + flattop_cosine_fall, cosine_rise_part + cosine_rise_part[::-1], rtol=1e-10)
    tanh_rise_part = (amp * 0.5 * (1 + np.tanh(np.linspace(-4, 4, rise_fall_length)))).tolist()
    assert np.allclose(flattop_tanh_rise + flattop_tanh_fall, tanh_rise_part + tanh_rise_part[::-1], rtol=1e-10)
    assert np.allclose(flattop_blackman_rise + flattop_blackman_fall, (amp * blackman(2*rise_fall_length)).tolist(), rtol=1e-10)


@pytest.mark.parametrize("pulse_length, v_start, v_end", list(zip(
    np.linspace(1, 30, 30).astype(int).tolist() + [10], np.linspace(0, 0.5, 30).tolist() + [-0.2], np.linspace(0.5, 0, 30).tolist() + [-0.2])))
def test_blackman_integral_waveform(pulse_length, v_start, v_end):
    waveform = blackman_integral_waveform(pulse_length, v_start, v_end)
    assert len(waveform) == pulse_length
    assert np.isclose(waveform[0], v_start, rtol=1e-10)
