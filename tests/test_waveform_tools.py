import numpy as np
import pytest
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


@pytest.mark.parametrize("length, sampling_rate", list(zip([16, 21, 60] * 2, [1e9, 1e9, 1e9, 2e9, 2e9, 2e9])))
def test_drag_no_drag_gaussian_to_scipy(length, sampling_rate):
    amp = 0.1
    sigma = length // 5
    I_wf, Q_wf = drag_gaussian_pulse_waveforms(
        amplitude=amp,
        length=length,
        sigma=sigma,
        alpha=0,
        anharmonicity=0,
        detuning=0,
        subtracted=False,
        sampling_rate=sampling_rate
    )
    I_sub_wf, Q_sub_wf = drag_gaussian_pulse_waveforms(
        amplitude=amp,
        length=length,
        sigma=sigma,
        alpha=0,
        anharmonicity=0,
        detuning=0,
        subtracted=True,
        sampling_rate=sampling_rate
    )
    gauss = amp * gaussian(int(length * sampling_rate/1e9), sigma * sampling_rate / 1e9)
    sub_gauss = gauss - gauss[0]
    assert (I_wf == gauss).all()
    assert (I_sub_wf == sub_gauss).all()


@pytest.mark.parametrize("length, sampling_rate", list(zip([16, 21, 60] * 2, [1e9, 1e9, 1e9, 2e9, 2e9, 2e9])))
def test_drag_no_detune_symmetric(length, sampling_rate):
    amp = 0.1
    sigma = length // 5
    I_gauss_wf, Q_gauss_wf = drag_gaussian_pulse_waveforms(
        amplitude=amp,
        length=length,
        sigma=sigma,
        alpha=0.1,
        anharmonicity=10e6,
        detuning=0,
        subtracted=False,
        sampling_rate=sampling_rate
    )
    I_cos_wf, Q_cos_wf = drag_cosine_pulse_waveforms(
        amplitude=amp, length=length, alpha=0.1, anharmonicity=10e6, detuning=0, sampling_rate=sampling_rate
    )

    I_gauss_first_half = I_gauss_wf[: int(length * sampling_rate / 1e9) // 2]
    Q_gauss_first_half = Q_gauss_wf[: int(length * sampling_rate / 1e9) // 2]
    if int(length * sampling_rate / 1e9) % 2 == 0:
        I_gauss_second_half = I_gauss_wf[int(length * sampling_rate / 1e9) // 2 :]
        Q_gauss_second_half = Q_gauss_wf[int(length * sampling_rate / 1e9) // 2 :]
    else:
        I_gauss_second_half = I_gauss_wf[int(length * sampling_rate / 1e9) // 2 + 1 :]
        Q_gauss_second_half = Q_gauss_wf[int(length * sampling_rate / 1e9) // 2 + 1 :]

    I_cos_first_half = I_cos_wf[: int(length * sampling_rate / 1e9) // 2]
    Q_cos_first_half = Q_cos_wf[: int(length * sampling_rate / 1e9) // 2]
    if int(length * sampling_rate / 1e9) % 2 == 0:
        I_cos_second_half = I_cos_wf[int(length * sampling_rate / 1e9) // 2 :]
        Q_cos_second_half = Q_cos_wf[int(length * sampling_rate / 1e9) // 2 :]
    else:
        I_cos_second_half = I_cos_wf[int(length * sampling_rate / 1e9) // 2 + 1 :]
        Q_cos_second_half = Q_cos_wf[int(length * sampling_rate / 1e9) // 2 + 1 :]

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
        anharmonicity=10e6,
        detuning=1e6,
        subtracted=True,
    )
    I_cos_wf, Q_cos_wf = drag_cosine_pulse_waveforms(
        amplitude=amp, length=length, alpha=0.1, anharmonicity=10e6, detuning=1e6
    )
    # plt.figure()
    # plt.plot(I_gauss_wf); plt.plot(Q_gauss_wf);
    # plt.figure()
    # plt.plot(I_cos_wf); plt.plot(Q_cos_wf);
    # fmt: off
    I_cos_wf_saved = [0.0, 0.0002769657232971771, 0.001104729603011983, 0.002473927583579785, 0.004369071873989109, 0.006768727952702063, 0.009645759497068654, 0.01296763840032217, 0.01669681628609918, 0.020791153219397854, 0.025204398652299072, 0.02988671904035681, 0.034785266028356264, 0.03984477863840703, 0.04500821250450123, 0.05021738889023198, 0.055413656003876606, 0.060538554990040634, 0.06553448293103396, 0.07034534523456083, 0.07491718991654327, 0.0791988165073115, 0.08314235261330107, 0.08670379155112135, 0.0898434849317776, 0.09252658460442116, 0.0947234289649252, 0.09640986928773972, 0.0975675324421131, 0.09818401709754303, 0.09825302129943794, 0.09777440009525856, 0.09675415270444514, 0.09520433954264555, 0.09314293022254534, 0.09059358445044334, 0.08758536851029725, 0.08415241076626882, 0.08033350031222729, 0.0761716335441403, 0.07171351402131555, 0.06700901150827748, 0.062110586544670235, 0.057072687270812765, 0.05195112553714429, 0.04680243954348848, 0.04168325038652503, 0.036649619939790434, 0.031756417449671566, 0.027056702103960273, 0.022601128618386163, 0.018437382593893804, 0.01460965202700875, 0.011158140912068843, 0.008118630362855208, 0.00552209210851163, 0.003394358591544375, 0.0017558532217350977, 0.000621383627087785, 8.355167010257165e-19]
    I_gauss_wf_saved = [0.0, 0.001073780904608826, 0.0023349628512836372, 0.0038042586821982497, 0.005502011193772566, 0.00744751100648014, 0.009658217829519757, 0.012148900938287308, 0.01493072187520801, 0.018010289561851744, 0.02138872469528336, 0.02506077596828639, 0.029014034760196674, 0.03322829697687259, 0.037675120229756776, 0.04231762120665081, 0.04711055173161783, 0.052000682663380426, 0.056927512682620696, 0.061824304634577526, 0.0666194361028255, 0.07123803415384893, 0.07560384770390176, 0.07964129578192236, 0.08327761714938726, 0.08644503725503276, 0.08908286314520077, 0.09113941627479812, 0.09257371742977398, 0.09335684711104869, 0.09347291833671084, 0.09291961617158861, 0.09170827839737786, 0.08986351339674249, 0.08742237323018005, 0.08443312070529434, 0.08095364772449766, 0.07704961727035359, 0.07279241221694462, 0.06825698021335344, 0.06351966497738867, 0.05865611060565444, 0.05373931740314083, 0.048837915978807656, 0.04401471185818555, 0.039325536665063034, 0.03481842509514958, 0.03053312047715684, 0.026500896611554758, 0.0227446705477413, 0.01927937055493589, 0.016112516085686382, 0.013244962125365307, 0.010671758862758797, 0.008383078827729089, 0.0063651671100978585, 0.0046012754994194625, 0.0030725478265279773, 0.0017588309044030217, 0.0006393927560509763]
    Q_cos_wf_saved = [0.0, 0.0010026402859392473, 0.0020044605248648157, 0.0030045712643328136, 0.004001945922244025, 0.004995356395647744, 0.005983313596089751, 0.006964014418684437, 0.007935296539064596, 0.008894602294394628, 0.009838952743862848, 0.010764932822994611, 0.011668688307569014, 0.012545935089979648, 0.013391981046890086, 0.014201760545521996, 0.014969881400536327, 0.015690683857968055, 0.016358310950819195, 0.01696678934644329, 0.01751011959242093, 0.01798237446874686, 0.018377803973148005, 0.01869094530631184, 0.01891673608751847, 0.019050628921100016, 0.019088705352388033, 0.01902778720004087, 0.018865543231123202, 0.018600589156840517, 0.018232578970743308, 0.017762285727362704, 0.01719166996699303, 0.016523934130592936, 0.015763561475967584, 0.014916338200502331, 0.013989357694307328, 0.012991006087871303, 0.01193092851702729, 0.01081997580170572, 0.009670131519824876, 0.008494419749765737, 0.007306794050053899, 0.006122008538878575, 0.004955472224623765, 0.003823088017390187, 0.002741078116344527, 0.0017257977145739706, 0.0007935391880745032, -3.967086506680151e-05, -0.0007582791986420062, -0.0013474154300067162, -0.0017931007096295606, -0.002082452700749313, -0.002203883991628183, -0.002147291072435667, -0.0019042310582648033, -0.0014680834292487904, -0.0008341941877387402, -2.149638238134954e-18]
    Q_gauss_wf_saved = [0.0017649357776302636, 0.0020923054995513114, 0.0024737989014702597, 0.0029133525887364417, 0.0034142575776329007, 0.003978931750140131, 0.004608684938262018, 0.005303486489155056, 0.006061746780172542, 0.006880125331179342, 0.0077533787419692135, 0.008674261527394754, 0.009633491929263247, 0.010619792899034747, 0.011620015677052578, 0.012619349819734761, 0.013601619294797886, 0.014549659593047045, 0.015445765967987489, 0.016272198226743816, 0.017011723291361316, 0.01764817335495194, 0.018166995163720962, 0.01855576499329099, 0.018804644400655227, 0.01890675386432293, 0.018858444906645982, 0.01865945604534522, 0.018312943667069002, 0.017825385294803008, 0.017206359319812087, 0.016468211652924804, 0.01562562549814072, 0.014695115189649062, 0.013694468464062054, 0.012642163465175249, 0.01155678711441125, 0.010456480258933303, 0.009358432374591157, 0.008278444790790759, 0.007230576729403481, 0.006226883264122815, 0.005277248977983215, 0.004389315976889983, 0.0035685003157239752, 0.002818087057980735, 0.0021393912907849387, 0.0015319705429630934, 0.0009938732122191287, 0.0005219077329892616, 0.00011191818419064529, -0.0002409463223308362, -0.0005419790093786122, -0.0007966876914736287, -0.0010105975618396757, -0.0011890877357667027, -0.0013372625792342613, -0.0014598569709010141, -0.0015611731435917224, -0.0016450456536731375]
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
            anharmonicity=0,
            detuning=0,
            subtracted=False,
        )
    with pytest.raises(
        Exception,
        match="Cannot create a DRAG pulse",
    ):
        drag_cosine_pulse_waveforms(
            amplitude=0.1, length=40, alpha=0.1, anharmonicity=0, detuning=0
        )


@pytest.mark.parametrize(
    "flat_length, rise_fall_length, sampling_rate",
    list(zip([0, 16, 16, 21, 21, 60, 60, 0, 16, 16, 21, 21, 60, 60], [8, 5, 10, 5, 10, 0, 10, 8, 5, 10, 5, 10, 0, 10], [1e9, 1e9, 1e9, 1e9, 1e9, 1e9, 1e9, 2e9, 2e9, 2e9, 2e9, 2e9, 2e9, 2e9])),
)
def test_flattop_flat_length(flat_length, rise_fall_length, sampling_rate):
    amp = 0.1

    flattop_gaussian = flattop_gaussian_waveform(amp, flat_length, rise_fall_length, sampling_rate=sampling_rate)
    flattop_cosine = flattop_cosine_waveform(amp, flat_length, rise_fall_length, sampling_rate=sampling_rate)
    flattop_tanh = flattop_tanh_waveform(amp, flat_length, rise_fall_length, sampling_rate=sampling_rate)
    flattop_blackman = flattop_blackman_waveform(amp, flat_length, rise_fall_length, sampling_rate=sampling_rate)
    flattop_gaussian_rise = flattop_gaussian_waveform(
        amp, flat_length, rise_fall_length, return_part="rise", sampling_rate=sampling_rate
    )
    flattop_cosine_rise = flattop_cosine_waveform(
        amp, flat_length, rise_fall_length, return_part="rise", sampling_rate=sampling_rate
    )
    flattop_tanh_rise = flattop_tanh_waveform(
        amp, flat_length, rise_fall_length, return_part="rise", sampling_rate=sampling_rate
    )
    flattop_blackman_rise = flattop_blackman_waveform(
        amp, flat_length, rise_fall_length, return_part="rise", sampling_rate=sampling_rate
    )
    flattop_gaussian_fall = flattop_gaussian_waveform(
        amp, flat_length, rise_fall_length, return_part="fall", sampling_rate=sampling_rate
    )
    flattop_cosine_fall = flattop_cosine_waveform(
        amp, flat_length, rise_fall_length, return_part="fall", sampling_rate=sampling_rate
    )
    flattop_tanh_fall = flattop_tanh_waveform(
        amp, flat_length, rise_fall_length, return_part="fall", sampling_rate=sampling_rate
    )
    flattop_blackman_fall = flattop_blackman_waveform(
        amp, flat_length, rise_fall_length, return_part="fall", sampling_rate=sampling_rate
    )

    assert np.allclose(
        flattop_gaussian,
        flattop_gaussian_rise + [amp] * int(flat_length * sampling_rate / 1e9) + flattop_gaussian_fall,
        rtol=1e-10,
    )
    assert np.allclose(
        flattop_cosine,
        flattop_cosine_rise + [amp] * int(flat_length * sampling_rate / 1e9) + flattop_cosine_fall,
        rtol=1e-10,
    )
    assert np.allclose(
        flattop_tanh,
        flattop_tanh_rise + [amp] * int(flat_length * sampling_rate / 1e9) + flattop_tanh_fall,
        rtol=1e-10,
    )
    assert np.allclose(
        flattop_blackman,
        flattop_blackman_rise + [amp] * int(flat_length * sampling_rate / 1e9) + flattop_blackman_fall,
        rtol=1e-10,
    )

    assert np.allclose(
        flattop_gaussian_rise + flattop_gaussian_fall,
        (amp * gaussian(int(np.round(2 * rise_fall_length * sampling_rate / 1e9)), rise_fall_length / 5 * sampling_rate / 1e9)).tolist(),
        rtol=1e-10,
    )
    cosine_rise_part = (
        amp * 0.5 * (1 - np.cos(np.linspace(0, np.pi, int(rise_fall_length * sampling_rate / 1e9))))
    ).tolist()
    assert np.allclose(
        flattop_cosine_rise + flattop_cosine_fall,
        cosine_rise_part + cosine_rise_part[::-1],
        rtol=1e-10,
    )
    tanh_rise_part = (
        amp * 0.5 * (1 + np.tanh(np.linspace(-4, 4, int(rise_fall_length * sampling_rate / 1e9))))
    ).tolist()
    assert np.allclose(
        flattop_tanh_rise + flattop_tanh_fall,
        tanh_rise_part + tanh_rise_part[::-1],
        rtol=1e-10,
    )
    assert np.allclose(
        flattop_blackman_rise + flattop_blackman_fall,
        (amp * blackman(2 * int(rise_fall_length * sampling_rate / 1e9))).tolist(),
        rtol=1e-10,
    )


@pytest.mark.parametrize(
    "pulse_length, v_start, v_end, sampling_rate",
    list(
        zip(
            np.linspace(2, 31, 30).astype(int).tolist(),
            np.linspace(-0.5, 0.5, 30).tolist(),
            np.linspace(0.5, -0.5, 30).tolist(),
            [1e9]*15 + [2e9]*15,
        )
    ),
)
def test_blackman_integral_waveform(pulse_length, v_start, v_end, sampling_rate):
    waveform = blackman_integral_waveform(pulse_length, v_start, v_end, sampling_rate)
    assert len(waveform) == int(pulse_length * sampling_rate / 1e9)
    assert np.isclose(waveform[0], v_start, rtol=1e-10)
    assert np.isclose(waveform[-1], v_end, rtol=1e-10)
