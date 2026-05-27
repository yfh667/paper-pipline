# Stochastic Geometry Analysis and Optimization for Multi-LEO Satellite-Assisted Communications

Xu Hu, Graduate Student Member, IEEE, Bin Lin, Senior Member, IEEE, Ping Wang, Fellow, IEEE, Xiao Lu, Member, IEEE, Weihua Zhuang, Fellow, IEEE, and Shuang Qi

Abstract—Low Earth orbit (LEO) satellites are vital in providing seamless connectivities to ground users (GUs). However, complex satellite-to-ground propagation and non-negligible satellite failure probabilities make single-satellite transmission unreliable. To address this issue, we consider a multi-LEOsatellite communication network (mLEO-CN), where a typical GU is served by multiple LEO satellites. The satellite locations are modeled as a binomial point process on a sphere and ordered according to their distances to the GU. To improve communication reliability, a serial communication scheme is adopted, in which the subsequent satellite is activated only when all preceding satellites fail to satisfy the target signalto-noise ratio threshold. By employing the tool of stochastic geometry, we derive key performance metrics, including overall transmission success probability, average transmission rate, and end-to-end delay under the serial communication scheme by incorporating both shadowed Rician (SR) fading and satellite failure probabilities. To improve analytical tractability, we derive asymptotic expressions for the end-to-end transmission success probability in two special cases by leveraging the asymptotic expression of the SR fading model and a Gamma-distribution, and further propose a cluster-based approximation approach for the overall transmission success probability. Building on these analyses, we formulate an optimization problem to maximize the ratio of the overall transmission success probability to the endto-end delay, and obtain its solution using a one-dimensional search approach. Numerical results validate the analysis, reveal the impact of key parameters, and identify the optimal number of serving LEO satellites under different constellation altitudes.

Index Terms—multi-LEO-satellite communication networks, stochastic geometry, cluster-based approximation approach.

# I. INTRODUCTION

N recent years, low Earth orbit (LEO) satellites have risen I as a promising solution for providing seamless network services in underserved areas, including deserts, oceans, and rural regions, thereby facilitating ubiquitous and high-capacity connectivities [1]. Currently, many LEO satellite constellation

The work was supported in part by the National Natural Science Foundation of China (No. 62371085) and in part by the Fundamental Research Funds for the Central Universities (No. 3132023514). An earlier version of this paper was accepted in part at the IEEE International Conference on Communications (ICC 2026), Glasgow, Scotland, UK, 2026. (Corresponding author: Bin Lin.) Xu Hu and Bin Lin are with the Information Science and Technology College, Dalian Maritime University, Dalian 116026, China (e-mail: huxu@dlmu.edu.cn; binlin@dlmu.edu.cn). Ping Wang is with the Department of Electrical Engineering and Computer Science, York University, Toronto, ON M3J 1P3, Canada (e-mail: pingw@yorku.ca). Xiao Lu is with the Research and Development, Ericsson, Ottawa, ON K2K 2V6, Canada (e-mail: xiao.lu@ericsson.com). Weihua Zhuang is with the Department of Electrical and Computer Engineering, University of Waterloo, Waterloo, ON N2L 3G1, Canada (e-mail: wzhuang@uwaterloo.ca). Shuang Qi is with the School of Electronic and Information Engineering, Liaoning University of Technology, Jinzhou 121001, China (e-mail: dxqishuang@lnut.edu.cn)

projects have launched a series of LEO satellites, driving various new services such as direct user-to-satellite communications and inter-satellite communications [2]. Despite these advancements, the complex and dynamic nature of the satelliteto-ground (as well as ground-to-satellite) propagation environment poses severe obstacles to maintaining high-quality links. Specifically, due to poor communication conditions, such as severe channel fading induced by signal scattering, these limitations make it difficult to meet traffic demands from ground users (GUs). Meanwhile, given the large scale of the constellation and the long operational lifespan of LEO satellites, they are increasingly vulnerable to threats stemming from various factors, such as high-energy particles, solar storms, component malfunctions, and anti-satellite weapons, resulting in temporarily disabling or permanently destroying satellites [3]. Consequently, communication reliability with LEO satellites decreases over time. Specifically, the reliability factor, initially at one, gradually decreases to 0.8 within two years and further drops to 0.6 within five years [4]. Therefore, reliance on a single satellite is highly vulnerable, as it suffers not only from unstable link quality but also from the potential for service interruption.

In light of these threats, constructing a multi-LEO satelliteassisted communication network (mLEO-CN), where a GU is served by multiple LEO satellites, is essential to enhance the reliability of LEO communication networks. This network leverages the enhanced signal strength from multiple LEO satellites, mitigating the limitations of poor signal reception from an individual satellite [5]. To quantitatively evaluate the performance benefits of multiple LEO satellites, it is vital to establish a theoretical framework for assessing the performance of mLEO-CN in comparison with the individual LEO satellite-served network.

Stochastic geometry is a potent mathematical instrument extensively utilized to characterize the system-level performance of large-scale wireless networks [6]. By adopting distribution models such as the binomial point process (BPP) and the Poisson point process (PPP) to represent the locations of network nodes, this methodology has provided valuable insights into critical performance metrics across various network domains. Recent applications of stochastic geometry in analyzing large-scale LEO satellite communication systems have underscored its utility in evaluating the performance of LEO satellite networks [7]–[9]. Building on this foundation, our objective is to construct an analytical framework, leveraging stochastic geometry, to characterize the network performance of the mLEO-CN and to delineate the effects of key network parameters on the end-to-end signal transmission performance.

# A. Related Works

Most existing studies concentrate on assessing network performance facilitated by an individual satellite, with particular emphasis on the nearest LEO satellite serving a GU. In the early stage, Yastrebova et al. analyzed the uplink coverage probability (CP) for a terrestrial–satellite network by modeling the distribution of LEO satellites as the uniform distribution along each orbit [10]. However, the computational complexity increases with the rising number of orbits in this model. Subsequently, the accuracy of modeling LEO satellite constellations as a BPP was validated by establishing a connection between the BPP and the Fibonacci lattice [7]. Furthermore, the contact distance distribution for the BPP on spherical surfaces was proposed in [11]. Building on these foundational studies, a growing number of studies have since explored the performance of LEO satellite networks using BPP models. In [7], Okati et al. constructed frameworks to capture the downlink CP and average data rate of a singlelayer LEO satellite network by employing the Rayleigh fading model. Then, Talgat et al. extended the single-layer LEO satellite network to a multi-layer spherical-shell architecture and conducted a corresponding coverage probability analysis [12]. To accurately describe the characteristics of the satelliteto-ground link, the precise outage probability was derived under the shadowed Rician (SR) fading model [13]. Since then, the performance analysis of modeling LEO satellites as BPPs and using the SR fading model has been explored gradually.

Since the received signal strength in a BPP model depends on each receiver’s location, the network performance of LEO satellite communication networks is influenced by each LEO satellite. Consequently, computational complexity increases with the number of LEO satellites, making performance analysis more challenging with a BPP model than with a homogeneous spherical PPPs (SPPPs) model [9]. To this end, the SPPP model has been applied to LEO satellite networks for tractable analysis. For instance, the downlink CP under the Nakagamim fading model was derived in [9] and the moments and meta-distribution of conditional CP were conducted in [14]. Despite a series of studies employing the SPPP to model the distribution of LEO satellites, the suitability of the SPPP model for LEO networks with finite areas and limited nodes remains controversial.

Currently, many complex distribution models have been introduced to accurately capture the practical characteristics of LEO satellite communication networks. Specifically, to account for the motion of LEO satellites in their orbital planes into the modeling of delay-tolerant data harvesting architectures, Choi utilized the Cox point process to represent the distribution of LEO satellites [15]. To accurately characterize the safety distance constraint for LEO satellites, Zhang et al. in [16] proposed a novel Poisson arc hardcore point process (PAHPP) model to precisely delineate the distribution of LEO satellites operating in circular orbits.

More recently, the research focus has gradually shifted from single-satellite services to communication networks enabled by multiple LEO satellites. Under coherent joint transmissions, Shang et al. derived the joint distance distribution between cooperative LEO satellites and a GU, thereby establishing a theoretical foundation for analyzing downlink coverage probability in coordinated transmission scenarios [17]. Building on this foundation, subsequent works extended the analysis to both downlink and uplink coverage performance [18], [19]. After that, Li et al. further extended this line of research to cell-free massive multiple-input multiple-output (MIMO) satellite communication networks [20]. On this basis, the concept of satellite cluster networks was introduced in [21], followed by the development of a mathematical framework for evaluating coverage probability under both coherent and non-coherent joint transmissions [21], [22]. Beyond communication performance, satellite clusters have also been applied to positioning services. For instance, by integrating multiple LEO satellites into existing medium Earth orbit (MEO)-based positioning systems, the K-availability and K-localizability probabilities were analyzed to quantify localization performance improvements [23]. Moreover, according to their functional roles within a cluster, LEO satellites can be categorized into leaders and followers, and a corresponding analytical framework was proposed to evaluate the communication performance of leader-follower satellite architectures [24]. For parallel transmissions, Qu et al. derived analytical expressions for the coverage probability and optimized satellite density to maximize this metric [25]. In addition, cooperative transmission based on coordinated beamforming among the several nearest satellites has been studied for further communication reliability enhancement. [26].

Despite significant progress in multi-satellite-assisted communications, most existing schemes, such as coherent joint transmission, non-coherent joint transmission, and parallel transmission, rely on the simultaneous participation of multiple LEO satellites, resulting in high energy consumption, considerable signaling overhead, and stringent synchronization and coordination requirements. In addition, satellite cluster networks generally require cluster formation, inter-satellite cooperation, and role assignment, which further increase implementation complexity in dynamic LEO environments. Motivated by these limitations, it is of great interest to develop a more efficient communication scheme for the mLEO-CN. In this context, the serial communication scheme is particularly promising, as it activates LEO satellites sequentially, from the nearest to the farthest, such that subsequent satellites are involved only when necessary. This scheme can improve resource utilization, reduce unnecessary energy costs, and enhance communication reliability with low implementation complexity. Nevertheless, the performance characterization of such mLEO-CNs remains challenging. First, the sequential involvement of multiple LEO satellites results in increasing complexity as the number of LEO satellites grows. Second, realistic satellite-to-ground (as well as ground-to-satellite) channels require the adoption of the SR fading model to capture scattering, reflection, diffraction, shadowing, and multipath effects, which further complicates the analysis. Third, the end-to-end performance depends on both uplink and downlink transmissions, making the characterization more difficult. Finally, existing studies rarely account for satellite failures caused by harsh space environments, despite their non-negligible impact on network reliability and performance. This drives our research to tackle the aforementioned challenges and bridge the existing gap.

# B. Contributions and Organization

In this paper, we consider an mLEO-CN, where a GU is served by multiple LEO satellites. To enhance communication reliability, we adopt a serial communication scheme in which LEO satellites provide network services to the GU sequentially, from the closest to the farthest, and each subsequent satellite is involved only if all preceding satellites fail to satisfy the predefined SNR threshold. The main technical contribution of this paper is the development of a tractable analytical framework for performance characterization under the serial communication scheme. On this basis, the asymptotic analysis, the cluster-based approximation approach, and optimization are complementary developments that enhance theoretical understanding, improve analytical tractability, and facilitate practical design of multi-LEO-satellite-assisted communication systems. To better reflect practical operating conditions, we incorporate failure probability into the stochastic geometry analysis of LEO satellite networks to capture satellite malfunctions in space environments. The contributions of this paper are summarized as follows.

• We develop a tractable analytical framework for the mLEO-CN to characterize the end-to-end transmission performance under the serial communication scheme. Specifically, by leveraging stochastic geometry and jointly accounting for channel fading and potential satellite failures, the proposed framework enables the evaluation of key performance metrics, including the overall transmission success probability, average transmission rate capacity, and end-to-end delay. To further improve analytical tractability and provide additional theoretical insight, we also derive asymptotic closed-form expressions for the end-to-end transmission success probability in two special cases.   
• Building upon the developed analytical framework, we further propose a cluster-based approximation approach to improve the tractability of evaluating the overall transmission success probability. In this approach, the serving LEO satellites are partitioned into multiple clusters, and the performance of each cluster is represented by that of its central satellite. Accordingly, the cumulative product associated with all serving satellites is approximated by the corresponding power of the representative satellite’s performance within each cluster, thereby significantly reducing computational complexity while maintaining high accuracy.   
• Extensive simulations are conducted to validate the proposed analytical framework and verify the accuracy of the derived exact and asymptotic expressions. In addition, the simulation results confirm the effectiveness of the proposed cluster-based approximation approach and illustrate the impact of key parameters, including constellation size, constellation altitude, predefined SNR threshold, and satellite failure probability, on the end-toend transmission performance.

![](images/0e18cda6abbdb25393908083fb597571932ee2d5d4b2ac061579cf24c4db3788.jpg)

<details>
<summary>text_image</summary>

LEO1
LEO2
LEO3
z
rmin
R1
R2
...
RK
LEOK
GU
Horizon
Earth
O
y
x
Operational LEO satellite
Malfunctioning LEO satellite
LEO satellite sphere
</details>

Fig. 1. A geometric structure of mLEO-CN.

• Based on the proposed analytical framework, we formulate an optimization problem to maximize the ratio of the overall transmission success probability to the end-to-end delay. The corresponding optimization results identify the optimal number of serving satellites at different constellation altitudes, thereby providing practical design guidance for LEO satellite networks.

The rest of this paper is organized as follows. Section II describes the system model, including the network model, communication scheme, channel model, and signal model. Section III derives the key transmission performance metrics for the mLEO-CN, including the overall transmission success probability, the average transmission rate capacity, and the end-to-end delay. Moreover, this section provides asymptotic expressions and an approximation approach for evaluating the overall transmission success probability. Section IV shows extensive numerical results and the solutions to the formulated optimization problem. Section V concludes this work.

# II. SYSTEM MODEL

# A. Network Model

We consider a multi-LEO-satellite communication network (mLEO-CN) that includes an LEO satellite constellation and a typical GU, as shown in Fig. 1. We establish a threedimensional space using the Cartesian coordinate system, where the Earth’s center is at the origin $O \triangleq ( 0 , 0 , 0 ) \in \mathbb { R } ^ { 3 }$ , the x-axis points towards a specific point on the equator, the y-axis is perpendicular to the x-axis and lies within the equatorial plane, and the z-axis points towards the geographic North Pole, perpendicular to the equatorial plane. Without loss of generality, the GU is located on the Earth’s surface at observation point $( 0 , 0 , r _ { \mathrm { e } } )$ [9] and can communicate directly with LEO satellites. In the LEO satellite constellation, there are N LEO satellites uniformly distributed on the sphere surface $\mathbb { S } _ { r _ { \mathrm { a } } } ^ { 2 }$ forming a BPP with radius of $r _ { \mathrm { a } } ,$ , where $r _ { \mathrm { a } } ~ = ~ r _ { \mathrm { e } } + r _ { \mathrm { m i n } }$ and $r _ { \mathrm { m i n } }$ is the constellation altitude and $\Phi _ { \mathrm { L E O } } = \left\{ s _ { 1 } , s _ { 2 } , . . . , s _ { N } \right\} \left( N \geq 1 , N \in \mathbb { N } ^ { + } \right)$ presents the set of LEO satellites. We rank LEO satellites in the mLEO-CN based on their distance to the GU, designating each of them as the $k ^ { \mathrm { t h } } \left( 1 \leq k \leq N \right)$ LEO satellite, from the closest to the farthest. Correspondingly, the distance between the $k ^ { \mathrm { t h } }$ LEO satellite and the GU is denoted as $R _ { k }$ . The GU can obtain the ordering of LEO satellites using satellite orbital data and ephemeris information in practical LEO satellite communication systems. Moreover, the maximum possible distance between the GU and an LEO satellite othe visible distance, is represented by $r _ { \mathrm { m a x } } { = } \sqrt { 2 r _ { \mathrm { e } } r _ { \mathrm { m i n } } + r _ { \mathrm { m i n } } ^ { 2 } }$ referred to as visible satellites, forming a subset of LEO satellites, denoted as $\Phi _ { \mathrm { v i s } } = \left\{ s _ { 1 } , s _ { 2 } , . . . , s _ { M } \right\} ( M \leq N ) \ [ 2 7 ]$ . In the mLEO-CN involving K LEO satellites, the serving satellites, denoted as $\Phi _ { s } { = } \left\{ s _ { 1 } , s _ { 2 } , { \ldots } , s _ { K } \right\} ( K \leq M )$ , are defined as a subset of K visible LEO satellites that are capable of communicating with the GU.

Signal transmissions in the mLEO-CN involve data transfer from the GU to an LEO satellite, followed by processing and subsequent feedback to the GU. To support this, K orthogonal frequency channels are allocated within the Kaband spectrum, and a decode-and-forward (DF) protocol is employed to facilitate the end-to-end signal transmissions [28]. To better characterize the operating state of an LEO satellite, we introduce a satellite failure probability $q _ { k }$ to quantify the likelihood of the $k ^ { \mathrm { t h } }$ LEO satellite malfunctions caused by potential threats such as solar storms, high-velocity collisions, and other space hazards. Accordingly, a malfunctioning satellite is treated as unavailable for transmission and is excluded from the set of serving satellites, while the communication scheme remains unchanged for the operational satellites.

# B. Communication Scheme

To enhance the communication reliability of LEO satellite communication networks, we implement a serial communication scheme with the serial probing mechanism in the mLEO-CN to regulate end-to-end signal transmissions. Specifically, the GU initially sends a pilot signal to the nearest LEO satellite over the first channel, where the satellite measures the received SNR. If the measured SNR exceeds a predefined threshold, the satellite responds by sending a feedback pilot signal to the GU on the same channel. The GU then evaluates the SNR of the returned signal. If the SNR at the GU also exceeds the predefined threshold, the GU selects the first LEO satellite for end-to-end signal transmissions. However, if the received SNR at either the first LEO satellite or the GU does not satisfy the threshold, the GU proceeds by sending a pilot signal to the second LEO satellite, and the same measurement and evaluation procedure is repeated to determine if the second satellite can be selected. This iterative procedure continues until a suitable LEO satellite is identified for transmission. If none of the K satellites in the mLEO-CN can satisfy the predefined SNR threshold requirement, the signal transmission process is terminated.

# C. Channel Model

1) Path-loss Model: A distance-dependent power path loss model is utilized to represent the path loss between the GU and the $k ^ { \mathrm { t h } }$ LEO satellite [29], that is, $\begin{array} { r } { L _ { k } \left( R _ { k } \right) = \bigg ( \frac { c } { 4 \pi f _ { c } } \bigg ) ^ { 2 } R _ { k } ^ { - \alpha } } \end{array}$ 2 , where $R _ { k }$ denote the distance between the $k ^ { \mathrm { t h } }$ LEO satellite and the GU, c is the light speed, $f _ { c }$ denotes carrier frequency of the signal, and α is the path loss exponent.   
2) Fading model: In a satellite-to-ground (and ground-tosatellite) channel, the SR fading model, widely validated in satellite communication systems, is adopted, with the cumulative distribution function (CDF) of the channel gain $\left| H \right| ^ { 2 }$ , described as [27], [30]

$$
F _ {| H | ^ {2}} (x) = 1 - \mu \sum_ {n = 0} ^ {m - 1} \mathcal {D} \sum_ {l = 0} ^ {n} \frac {n !}{l !} \mathcal {J} x ^ {l} \mathrm{e} ^ {- (\beta - \delta) x}, \tag {1}
$$

where $\begin{array} { r } { \frac { 1 } { 2 b _ { \mathrm { s } } } \Big ( \frac { 2 b _ { \mathrm { s } } m } { 2 b _ { \mathrm { s } } m + \Omega } \Big ) ^ { m } , \delta = \frac { 1 } { 2 b _ { \mathrm { s } } } \Big ( \frac { \Omega } { 2 b _ { \mathrm { s } } m + \Omega } \Big ) , \beta = \frac { 1 } { 2 b _ { \mathrm { s } } } } \end{array}$ $\begin{array} { r } { \mathcal { D } { = } \frac { ( 1 - m ) _ { n } ( - \delta ) ^ { n } } { ( n ! ) ^ { 2 } } , \mathcal { I } { = } ( \beta - \delta ) ^ { - ( n + 1 - l ) } } \end{array}$ (n!)2 m 1 . Moreover, with Ω, m and $\mu =$ 2bs 2bs $b _ { \mathrm { s } }$ being the average power of the line-of-sight (LoS) component, the Nakagami parameter and the half average power of the multi-path components except the LoS component. In addition, $( x ) _ { n }$ is the Pochhammer symbol. Accordingly, the probability density function (PDF) of the channel gain $\left| H \right| ^ { 2 }$ under SR fading is expressed as [30]

$$
f _ {| H | ^ {2}} (x) = \mu \sum_ {n = 0} ^ {m - 1} \mathcal {D} x ^ {n} \mathrm{e} ^ {- (\beta - \delta) x}. \tag {2}
$$

# D. Signal Model

For the uplink signal transmission from the GU to the $k ^ { \mathrm { t h } }$ LEO satellite, the received SNR at the $k ^ { \mathrm { t h } }$ LEO satellite is expressed as

$$
\mathrm{SNR} _ {k} ^ {\mathrm{u}} = \frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} L _ {k} \left(R _ {k}\right) \left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}}{\sigma_ {k} ^ {2}}, \tag {3}
$$

where $p _ { \mathrm { u } }$ is the transmit power of the GU, $G _ { k } ^ { \mathrm { u } }$ presents the uplink antenna gain. In the mLEO-CN, each satellite is equipped with a directional antenna that emits a main lobe, directing one beam towards the center of the Earth. The GU is located within the beam of each LEO satellite, while the GU has an antenna to communicate with LEO satellites. Consequently, $G _ { k } ^ { \mathrm { u } } = G _ { \mathrm { u } } ^ { \mathrm { t } } G _ { \mathrm { s } , k } ^ { \mathrm { r } } ,$ where $G _ { \mathrm { u } } ^ { \mathrm { t } }$ is the transmit antenna gain of the GU, and $G _ { \mathrm { s } , k } ^ { \mathrm { r } }$ presents the receive antenna gain of the $k ^ { \mathrm { t h } }$ LEO satellite. Moreover, $\sigma _ { k } ^ { 2 }$ is the received noise power in the $k ^ { \mathrm { t h } }$ channel, $\left| H _ { k } ^ { \mathrm { u } } \right| ^ { 2 }$ denotes the power gain of the uplink channel from the GU to the $k ^ { \mathrm { t h } }$ LEO satellite, and the channel gains of the K uplink channels between the GU and K LEO satellites are mutually independent random variables. According to [31], numerical results show that the interference power in satellite communication is significantly lower than the noise power. Additionally, the ample bandwidth in satellite communications and the employed narrow beam transmission modes can enable orthogonal frequency allocation, thereby reducing co-channel interference in the mLEO-CN [32]. Therefore, as with most existing studies [13], [31], [33], we assume a noise-dominated propagation environment where co-channel interference is considered negligible. Accordingly, this assumption is more appropriate for scenarios in which spectrum resources are relatively abundant and communication reliability is prioritized over aggressive frequency reuse.

Accordingly, for the downlink signal transmission from the $k ^ { \mathrm { t h } }$ LEO satellite to the GU, the received SNR at the GU is given by

$$
\mathrm{SNR} _ {k} ^ {\mathrm{d}} = \frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} L _ {k} (R _ {k}) \left| H _ {k} ^ {\mathrm{d}} \right| ^ {2}}{\sigma_ {k} ^ {2}}, \tag {4}
$$

where downlink antenna gain, which is expressed as $p _ { \mathrm { s } }$ is the transmit power of each LEO satellite, $G _ { k } ^ { \mathrm { d } } = \ddot { G } _ { \mathrm { s } , k } ^ { \mathrm { t } } G _ { \mathrm { u } } ^ { \mathrm { r } } ,$ $G _ { k } ^ { \mathrm { d } }$ Gts,k is the where $G _ { \mathrm { s } , k } ^ { \mathrm { t } }$ k is the transmit antenna gain of the $k ^ { \mathrm { t h } }$ uLEO satellite, $G _ { \mathrm { u } } ^ { \mathrm { r } }$ is the receive antenna gain of the GU. Similarly, $\left| H _ { k } ^ { \mathrm { d } } \right| ^ { 2 }$ represents the power gain of the downlink channel from the $\dot { k } ^ { \mathrm { t h } }$ LEO satellite to the GU, and the channel gains of the $K$ downlink channels between K LEO satellites and the GU are mutually independent random variables.

# E. Distance distribution

To facilitate the derivation of subsequent analytical expressions, we adopt the following distance distribution [34].

Lemma 1. The PDF of distance $R _ { k }$ between the $k ^ { \mathrm { t h } }$ LEO satellite and the GU is given by

$$
f _ {R _ {k}} \left(r _ {k}\right) = \frac {1}{\Xi} \sum_ {l = 0} ^ {k - 1} \sum_ {n = 0} ^ {N - k} \frac {\psi}{\Theta} r _ {k} ^ {2 n + 2 l + 1}, \tag {5}
$$

for $r _ { \operatorname* { m i n } { } } ~ \le ~ r _ { k } ~ \le ~ r _ { \operatorname* { m a x } { } }$ and $k \in \{ 1 , 2 , 3 , . . . , K \}$ , where rmin is the constellation altitude, $r _ { \mathrm { m a x } }$ denotes the maximum possible distance between the GU and an visible satellite, $\begin{array} { r l r } { \stackrel {  } { \Theta } } & { = } & { ( \frac { - r _ { \mathrm { m i n } } ^ { 2 } } { 4 r _ { \mathrm { e } } r _ { a } } ) ^ { l - k + 1 } ( 1 + \frac { r _ { \mathrm { m i n } } ^ { 2 } } { 4 r _ { \mathrm { e } } r _ { a } } ) ^ { n + k - N } ( 4 r _ { \mathrm { e } } r _ { a } ) ^ { n + l + 1 } , } \end{array}$ 4rera (4rera)n+l+1,

$$
\Xi = \sum_ {j = k} ^ {N} \binom{N}{j} \left(\frac {r _ {\max} ^ {2} - r _ {\min} ^ {2}}{4 r _ {\mathrm{e}} r _ {a}}\right) ^ {j} \left(1 - \frac {r _ {\max} ^ {2} - r _ {\min} ^ {2}}{4 r _ {\mathrm{e}} r _ {a}}\right) ^ {N - j}, a n d
$$

$$
\psi = 2 N \binom{N - 1}{k - 1} \binom{N - k}{n} \binom{k - 1}{l} (- 1) ^ {n}.
$$

# III. PERFORMANCE ANALYSIS

# A. Exact Overall Transmission Success Probability

The transmission success probability is defined as the probability that the received SNR is larger than a predefined threshold τ , expressed as $P \left( \tau \right) \stackrel { \Delta } { = } \mathbb { P } \left( \mathrm { S N R } > \tau \right)$ . For the endto-end signal transmission, which includes the uplink from the GU to the $k ^ { \mathrm { t h } }$ LEO satellite and the downlink from the $k ^ { \mathrm { t h } }$ LEO satellite to the GU, the end-to-end transmission success probability represents the probability that the received SNR at both the LEO satellite and the GU satisfies the predefined threshold τ , which is expressed as

$$
P _ {k} (\tau) \triangleq \mathbb {P} \left(\mathrm{SNR} _ {k} ^ {\mathrm{u}} > \tau , \mathrm{SNR} _ {k} ^ {\mathrm{d}} > \tau\right), \tag {6}
$$

where $\mathrm { S N R } _ { k } ^ { \mathrm { u } }$ and $\mathrm { S N R } _ { k } ^ { \mathrm { d } }$ denote the received SNR at the $k ^ { \mathrm { t h } }$ LEO satellite and the GU, respectively.

Under the adopted serial communication scheme, the GU probes serving satellites sequentially in the prescribed order, and a subsequent satellite is activated only if all preceding satellites fail to satisfy the target SNR threshold. Accordingly, the overall transmission success probability for K serving satellites can be expressed as

$$
\begin{array}{l} P _ {\mathrm{s}} (\tau) = P _ {1} (\tau) + (1 - P _ {1} (\tau)) P _ {2} (\tau) \\ + \left(1 - P _ {1} (\tau)\right) \left(1 - P _ {2} (\tau)\right) P _ {3} (\tau) \\ + \dots + \left(\prod_ {j = 1} ^ {K - 1} \left(1 - P _ {j} (\tau)\right)\right) P _ {K} (\tau) \tag {7} \\ \Leftrightarrow 1 - \prod_ {k = 1} ^ {K} (1 - P _ {k} (\tau)), \\ \end{array}
$$

where $P _ { k } \left( \tau \right)$ denotes the transmission success probability through the $\dot { k } ^ { \mathrm { t h } }$ LEO satellite. By De Morgan’s law, the above serial-form expression is mathematically equivalent to a compact complement form, i.e., one minus the probability that all K serving satellites fail.

To account for the effect of satellite failure, the end-toend transmission success probability for each satellite should be multiplied by a factor (1−qk) representing the probability of the $\hat { k } ^ { \mathrm { { t h } } }$ LEO satellite being operational. Accordingly, by incorporating the satellite failure probability into the equivalent complement-form representation, the overall transmission success probability under the adopted serial communication scheme is given in Theorem 1.

Theorem 1. For the serial communication supported by K LEO satellites, the overall transmission success probability is expressed as

$$
P _ {\mathrm{s}} (\tau) = 1 - \prod_ {k = 1} ^ {K} \left(1 - \bar {q} _ {k} P _ {k} (\tau)\right), \tag {8}
$$

where $\overline { { q } } _ { k } = 1 - q _ { k }$ with $q _ { k }$ being the failure probability of the $k ^ { \mathrm { t h } }$ LEO satellite. Moreover, $P _ { k } \left( \tau \right)$ is expressed in $( 9 ) ,$ at the top of the next page, where $\scriptstyle { \mathcal { G } } = { \frac { \sigma _ { k } ^ { 2 } ( 4 \pi f _ { c } ) ^ { 2 } } { c ^ { 2 } } }$ c 2 . In addition, $f _ { R _ { k } } \left( r _ { k } \right)$ is the PDF of the distance between the $k ^ { \mathrm { t h } }$ LEO satellite and the GU, as given in Lemma 1.

The Proof of Theorem 1 is given in Appendix A.

# B. Asymptotic Overall Transmission Success Probability

Due to the complexity of the CDF of the SR fading model and the PDF of the distance between the $k ^ { \mathrm { t h } }$ LEO satellite and the GU, deriving a closed-form expression for the exact overall transmission success probability poses significant challenges. Therefore, to gain deeper insights, we derive asymptotic expressions for the overall transmission success probability in specific cases.

Case 1: For the high SNR regime $( \mathrm { S N R }  \infty )$ , we have $x \to 0 .$ . The asymptotic CDF of the SR fading model can be expressed as F ∞|H|2 (x) ≈ µx [35]. $F _ { | H | ^ { 2 } } ^ { \infty } \left( x \right) \approx \mu x$

$$
F _ {| H | ^ {2}} ^ {\infty} (x) \approx \mu x. \tag {10}
$$

$$
\begin{array}{l} P _ {k} (\tau) = \int_ {r _ {\min}} ^ {r _ {\max}} \left(\mu \sum_ {n = 0} ^ {m - 1} \mathcal {D} \sum_ {l = 0} ^ {n} \mathcal {J} \left(\frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right) ^ {l} \exp \left(- \frac {(\beta - \delta) \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right) \mu \sum_ {n = 0} ^ {m - 1} \mathcal {D} \sum_ {l = 0} ^ {n} \mathcal {J} \left(\frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right) ^ {l} \exp \left(- \frac {(\beta - \delta) \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right)\right) \tag {9} \\ \times f _ {R _ {k}} \left(r _ {k}\right) d r _ {k}. \\ \end{array}
$$

Corollary 1. The end-to-end transmission success probability through the $k ^ { \mathrm { t h } }$ LEO satellite at high SNR regime can be approximated as

$$
\begin{array}{l} P _ {k} ^ {\infty} (\tau) \approx 1 + \frac {\mu^ {2} \tau^ {2} \mathcal {G} ^ {2}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \Xi} \sum_ {l = 0} ^ {k - 1} \sum_ {n = 0} ^ {N - k} \frac {\psi}{\Theta} \left(\frac {r _ {\max} ^ {2 \alpha + \Delta} - r _ {\min} ^ {2 \alpha + \Delta}}{2 \alpha + \Delta}\right) \\ - \frac {\mu \tau \mathcal {G}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \Xi} \sum_ {l = 0} ^ {k - 1} \sum_ {n = 0} ^ {N - k} \frac {\psi}{\Theta} \left(\frac {r _ {\max} ^ {\alpha + \Delta} - r _ {\min} ^ {\alpha + \Delta}}{\alpha + \Delta}\right) \\ - \frac {\mu \tau \mathcal {G}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \Xi} \sum_ {l = 0} ^ {k - 1} \sum_ {n = 0} ^ {N - k} \frac {\psi}{\Theta} \left(\frac {r _ {\max} ^ {\alpha + \Delta} - r _ {\min} ^ {\alpha + \Delta}}{\alpha + \Delta}\right), \tag {11} \\ \end{array}
$$

where $\Delta = 2 n + 2 l + 2 .$

The Proof of Corollary 1 is given in Appendix B.

Case 2: The SR fading model can be approximated by a Gamma distribution, $\textit { G } \sim \Gamma \left( \alpha _ { s } , \beta _ { s } \right)$ , with shape and scale parameters $\alpha _ { s }$ and $\beta _ { s }$ [29], [36]. The corresponding approximate CDF is given by

$$
F _ {| H | ^ {2}} (x) \approx \gamma \left(\alpha_ {s}, \frac {x}{\beta_ {s}}\right) / \Gamma \left(\alpha_ {s}\right), \tag {12}
$$

where αs = m(2bs+Ω)4mbs2+4mbsΩ+Ω2 $\begin{array} { r } { \alpha _ { s } = \frac { m ( 2 b _ { \mathrm { s } } + \Omega ) ^ { 2 } } { 4 m b _ { \mathrm { s } } ^ { 2 } + 4 m b _ { \mathrm { s } } \Omega + \Omega ^ { 2 } } } \end{array}$ and β = 4mbs2+4mbsΩ+Ω2 . $\begin{array} { r } { \beta _ { s } = \frac { 4 m { b _ { \mathrm { s } } } ^ { 2 } + 4 m { b _ { \mathrm { s } } } \Omega + \Omega ^ { 2 } } { m ( 2 b _ { \mathrm { s } } + \Omega ) } } \end{array}$

Corollary 2. Based on this approximation, the end-to-end transmission success probability can be simplified as

$$
\begin{array}{l} P _ {k} ^ {\mathrm{app}} (\tau) \approx \frac {1}{\Xi} \sum_ {l = 0} ^ {k - 1} \sum_ {n = 0} ^ {N - k} \sum_ {t _ {1} = 0} ^ {\widetilde {\alpha_ {s}} - 1} \sum_ {t _ {2} = 0} ^ {\widetilde {\alpha_ {s}} - 1} \frac {\psi}{\Theta} \frac {\left(\frac {\tau \mathcal {G}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right) ^ {t _ {1}} \left(\frac {\tau \mathcal {G}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right) ^ {t _ {2}}}{\alpha \Gamma (t _ {1} + 1) \Gamma (t _ {2} + 1)} \\ \times \left(\frac {r _ {\min} ^ {\mathrm{B}} \Gamma \left(\frac {\mathrm{B}}{\alpha} \mathrm{A} r _ {\min} ^ {\alpha}\right)}{\left(\mathrm{A} r _ {\min} ^ {\alpha}\right) ^ {\frac {\mathrm{B}}{\alpha}}} - \frac {r _ {\max} ^ {\mathrm{B}} \Gamma \left(\frac {\mathrm{B}}{\alpha} \mathrm{A} r _ {\max} ^ {\alpha}\right)}{\left(\mathrm{A} r _ {\max} ^ {\alpha}\right) ^ {\frac {\mathrm{B}}{\alpha}}}\right). \tag {13} \\ \end{array}
$$

where $\begin{array} { r } { \mathrm { A } = \Big ( \frac { \mathcal { G } } { p _ { \mathrm { u } } G _ { k } ^ { \mathrm { u } } } + \frac { \mathcal { G } } { p _ { \mathrm { s } } G _ { k } ^ { \mathrm { d } } } \Big ) , \mathrm { B } = ( t _ { 1 } + t _ { 2 } ) } \end{array}$ , and $\widetilde { \alpha _ { s } }$ represents an approximate integer $o \ b { f } \alpha _ { s } ,$ , that is $\widetilde { \alpha _ { s } } = \left\lfloor \alpha _ { s } \right\rfloor o r \left\lceil \alpha _ { s } \right\rceil$ .

The Proof of Corollary 2 is given in Appendix C.

C. Cluster-based Approximation Approach for Complexity $R e \mathrm { . }$ duction

The aforementioned asymptotic expression only simplifies the end-to-end transmission success probability for each LEO satellite individually. However, the computational complexity of the overall success probability still increases dramatically as the number of serving satellites grows. To address this, we propose a cluster-based approximation approach to estimate the overall transmission success probability for $K > 2$ . Instead of evaluating each satellite individually, the core idea of the cluster-based approximation is to divide the serving LEO satellites into multiple clusters and represent the performance of each cluster using its central satellite. This approach simplifies the cumulative product of each satellite’s performance by approximating it as the power of the central satellite’s performance, effectively reducing computational complexity without significantly sacrificing accuracy.

Proposition 1. The overall transmission success probability based on the cluster-based approximation approach is expressed as

$$
\begin{array}{l} P _ {s} ^ {\text {app}} (\tau) \approx 1 - \left(\prod_ {j = 1} ^ {\lfloor K / \mathcal {K} \rfloor} \left(1 - \overline {{q}} _ {k} P _ {(j - 1) \mathcal {K} + \lfloor \frac {\mathcal {K} + 1}{2} \rfloor} (\tau)\right) ^ {\mathcal {K}}\right) \\ \times \left(1 - \overline {{q}} _ {k} P _ {\lfloor K / \mathcal {K} \rfloor + \lfloor \frac {\mathrm{mod} (K , \mathcal {K}) + 1}{2} \rfloor} (\tau)\right) ^ {\mathrm{mod} (K, \mathcal {K})}, \tag {14} \\ \end{array}
$$

$f o r K > 2 ,$ , where $\mathcal { K } ( \mathcal { K } \leq K , \mathcal { K } \in \mathbb { N } ^ { + } )$ is the cluster size, and $\lfloor \cdot \rfloor$ denotes the floor operation, and mod $( u , v ) ( u , v \in \mathbb { N } ^ { + } )$ denotes the remainder of the Euclidean division of u by v.

Proof: Since the performance of all LEO satellites in each cluster is represented by the power of the central satellite’s performance, thus $P _ { k } \left( \tau \right)$ in (8) is replaced by $P _ { ( j - 1 ) K + \left\lfloor \frac { \kappa + 1 } { 2 } \right\rfloor }$ in the first line of (14) to denote the central satellite of each cluster. Then, the $\mathcal { K } ^ { \mathrm { t h } }$ power of this item is used to represent the performance of all satellites in each cluster. Subsequently, the K accumulative multiplications are reduced to $\lfloor K / \kappa \rfloor$ to reflect the cumulative effect of K central satellites. In addition, since K is typically not an exact multiple of $\kappa ,$ a similar way is employed in the second line of (14) to account for the remainder of LEO satellites. □

To compare the mathematical complexity of the original expression in (8) with the proposed approximation approach in (14), we quantify them through the number of integrals and multiplications [37]. Since the end-to-end transmission success probability for each LEO satellite involves one integral, in (8), the overall transmission success probability for the serial communication with K LEO satellites consists of K integrals and K multiplications. In contrast, in the proposed clusterbased approximation approach, the number of integrals is reduced to K and the number of multiplications decreases to K $\frac { \ d { } K } { \ d { } K }$ . Therefore, compared to the original expression, the proposed approach significantly reduces mathematical complexity.

# D. Average Transmission Rate Capacity

The performance measure of the transmission rate capacity is defined as the ergodic capacity from the Shannon-Hartley theorem, given by $C \triangleq B \log _ { 2 } { ( 1 + \mathrm { S N R } ) }$ , where B is the bandwidth. For the end-to-end transmission involving the uplink from the GU to the $k ^ { \mathrm { t h } }$ LEO satellite and the downlink from the $k ^ { \mathrm { t h } }$ LEO satellite to the GU, the end-toend transmission rate capacity through the $k ^ { \mathrm { t h } }$ LEO satellite

$$
\begin{array}{l} C _ {k} = B \int_ {r _ {\min}} ^ {r _ {\max}} \int_ {0} ^ {\infty} \int_ {0} ^ {\infty} \log_ {2} \left(1 + \min \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| h _ {k} ^ {\mathrm{u}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}}, \frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| h _ {k} ^ {\mathrm{d}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}}\right)\right) \mathbb {1} \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| h _ {k} ^ {\mathrm{u}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) \tag {17} \\ \times \mathbb {1} \left(\frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| h _ {k} ^ {\mathrm{d}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) f _ {\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{u}}\right) f _ {\left| H _ {k} ^ {\mathrm{d}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{d}}\right) d h _ {k} ^ {\mathrm{u}} d h _ {k} ^ {\mathrm{d}} f _ {R _ {k}} \left(r _ {k}\right) d r _ {k}. \\ \end{array}
$$

depends on the minimum of the received SNR at the $k ^ { \mathrm { t h } }$ LEO satellite and the received SNR at the GU, which is given by

$$
C _ {k} \triangleq B \log_ {2} \left(1 + \min \left(\mathrm{SNR} _ {k} ^ {\mathrm{u}}, \mathrm{SNR} _ {k} ^ {\mathrm{d}}\right)\right). \tag {15}
$$

In the mLEO-CN, the average transmission rate capacity is defined as the effective end-to-end transmission rate capacity across K LEO satellites, starting from the first, where each subsequent satellite is included only if all previous LEO satellites cannot meet the predefined SNR threshold.

Theorem 2. The average transmission rate capacity for the serial communication supported by K LEO satellites mLEO-CN is expressed as

$$
C _ {\mathrm{s}} = \left\{ \begin{array}{l} \bar {q} _ {k} C _ {1}, \quad K = 1, \\ \bar {q} _ {k} C _ {1} + \sum_ {k = 2} ^ {K} \bar {q} _ {k} C _ {k} \prod_ {j = 1} ^ {k - 1} (1 - P _ {j} (\tau)), K \geq 2, \end{array} \right. \tag {16}
$$

where $P _ { j } \left( \tau \right)$ denotes the end-to-end transmission success probability through the $j ^ { \mathrm { t h } }$ LEO satellite, and $C _ { 1 }$ and $C _ { k }$ are the transmission rate capacities through the first and $k ^ { \mathrm { t h } }$ LEO satellites, respectively, $C _ { k }$ is expressed in (17), on top of this page. In (17), 1 (·) denotes an indicator function, $f _ { \left| H _ { k } ^ { \mathrm { u } } \right| ^ { 2 } } \left( h _ { k } ^ { \mathrm { u } } \right)$ and $f _ { \left| H _ { k } ^ { \mathrm { d } } \right| ^ { 2 } } \left( h _ { k } ^ { \mathrm { d } } \right)$ are the PDFs of the SR fading in the uplink and downlink of the $k ^ { \mathrm { t h } }$ channel, respectively, as given in (2).

The Proof of Theorem 2 is given in Appendix D.

# E. End-to-End Delay

In the mLEO-CN, the end-to-end delay is considered to be composed of transmission delay and the handover delay. The transmission delay characterizes the time required for message delivery between the GU and the $k ^ { \mathrm { t h } }$ LEO satellite, expressed as the sum of the uplink delay $T _ { k } ^ { \mathrm { u } }$ from the GU to the $k ^ { \mathrm { t h } }$ LEO satellite and the downlink delay $T _ { k } ^ { \mathrm { d } }$ from the $k ^ { \mathrm { t h } }$ LEO satellite to the GU. Moreover, when employing the serial communication scheme, a handover delay arises when the current LEO satellite cannot satisfy the predefined SNR threshold, necessitating a switch to an alternative LEO satellite. Notably, as the number of switches increases, the cumulative handover delay becomes non-negligible. For analytical tractability, the handover delay $T _ { \mathrm { h o } }$ per switch is assumed to be a constant and the cumulative handover delay incurred when switching from the first LEO satellite to the $k ^ { \mathrm { t h } }$ LEO satellite is calculated as $( k - 1 ) T _ { \mathrm { h o } }$ . Thus, the total delay through the $k ^ { \mathrm { t h } }$ LEO satellite is

$$
T _ {k} \triangleq T _ {k} ^ {\mathrm{u}} + T _ {k} ^ {\mathrm{d}} + (k - 1) T _ {\mathrm{ho}}. \tag {18}
$$

Therefore, by employing the serial communication scheme involving K serving LEO satellites, the end-to-end delay is defined as the average of the total delay through any of the K LEO satellites that successfully transmit the message data.

Theorem 3. The end-to-end delay for the serial communication supported by K LEO satellites in the mLEO-CN is expressed as

$$
T _ {\mathrm{s}} = \left\{ \begin{array}{l l} \frac {T _ {1}}{P _ {1} (\tau)}, & K = 1, \\ \frac {T _ {1} + \sum_ {k = 2} ^ {K} T _ {k} \prod_ {j = 1} ^ {k - 1} \left(1 - P _ {j} (\tau)\right)}{1 - \prod_ {k = 1} ^ {K} \left(1 - P _ {k} (\tau)\right)}, & K \geq 2, \end{array} \right. \tag {19}
$$

where $T _ { 1 }$ and $T _ { k }$ denote the total delay through the first and the $k ^ { \mathrm { t h } }$ LEO satellites, respectively. Note that, $T _ { k }$ is expressed in (20), on top of the next page, where $\omega$ is the length of the message packet.

The Proof of Theorem 3 is given in Appendix E.

# F. Optimal Number of Serving LEO Satellites

Although the serial communication supported by multiple LEO satellites can improve the overall transmission success probability, it also introduces extra handover delays at each switch, resulting in a significant increase in the end-to-end delay. To balance the overall performance of mLEO-CN, based on the derived analytical results presented in Section III, we formulate an optimization problem to maximize the ratio of the overall transmission success probability to the end-to-end delay, as given in (21) at the top of the next page. Our objective is to find the optimal number of serving LEO satellites $K ^ { \star }$ under the maximum $\eta ,$ formulated as

$$
(\mathbf {P 1}): \quad K ^ {\star} = \arg \max _ {K} \eta \tag {22}
$$

$$
\text { s.t. } \quad \Phi_ {\text { vis }}, \Phi_ {s} \neq \phi \tag {22a}
$$

$$
K \in \mathbb {N} ^ {+}, K \leq N, \tag {22b}
$$

$$
r _ {1} \leq r _ {\min} \leq r _ {\mathrm{u}}, \tag {22c}
$$

$$
P _ {s} (\tau), P _ {k} (\tau), q \in [ 0, 1 ], \tag {22d}
$$

In problem (P1), constraint (22a) ensures that both the sets of visible satellites and serving satellites are non-empty. Constraint (22b) specifies that the constellation size and the number of serving LEO satellites must be positive integers and enforces that the number of serving LEO satellites does not exceed the constellation size. Additionally, constraint (22c) defines the permissible range for the constellation altitude, which varies from $r _ { 1 }$ to $r _ { \mathrm { u } } .$ Lastly, constraint (22d) ensures that both the overall transmission success probability and the end-to-end transmission success probability via the $k ^ { \mathrm { t h } }$ LEO satellite fall within the range of zero to one.

$$
\begin{array}{l} T _ {k} = \int_ {r _ {\min}} ^ {r _ {\max}} \int_ {0} ^ {\infty} \int_ {0} ^ {\infty} \frac {\omega \mathbb {1} \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| h _ {k} ^ {\mathrm{u}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right)}{B \log_ {2} \left(1 + \frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| h _ {k} ^ {\mathrm{u}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}}\right)} \mathbb {1} \left(\frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| h _ {k} ^ {\mathrm{d}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) f _ {\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{u}}\right) f _ {\left| H _ {k} ^ {\mathrm{d}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{d}}\right) f _ {R _ {k}} \left(r _ {k}\right) d h _ {k} ^ {\mathrm{u}} d h _ {k} ^ {\mathrm{d}} d r _ {k} \\ + \int_ {r _ {\min}} ^ {r _ {\max}} \int_ {0} ^ {\infty} \int_ {0} ^ {\infty} \frac {\omega \mathbb {1} \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| h _ {k} ^ {\mathrm{u}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right)}{B \log_ {2} \left(1 + \frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| h _ {k} ^ {\mathrm{d}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}}\right)} \mathbb {1} \left(\frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| h _ {k} ^ {\mathrm{d}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) f _ {\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{u}}\right) f _ {\left| H _ {k} ^ {\mathrm{d}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{d}}\right) f _ {R _ {k}} \left(r _ {k}\right) d h _ {k} ^ {\mathrm{u}} d h _ {k} ^ {\mathrm{d}} d r _ {k} \\ + \int_ {r _ {\min}} ^ {r _ {\max}} \int_ {0} ^ {\infty} \int_ {0} ^ {\infty} (k - 1) T _ {\mathrm{ho}} \mathbb {1} \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} | h _ {k} ^ {\mathrm{u}} | ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) \mathbb {1} \left(\frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} | h _ {k} ^ {\mathrm{d}} | ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) f _ {| H _ {k} ^ {\mathrm{u}} | ^ {2}} (h _ {k} ^ {\mathrm{u}}) f _ {| H _ {k} ^ {\mathrm{d}} | ^ {2}} (h _ {k} ^ {\mathrm{d}}) f _ {R _ {k}} (r _ {k}) \\ \times d h _ {k} ^ {\mathrm{u}} d h _ {k} ^ {\mathrm{d}} d r _ {k}. \tag {20} \\ \end{array}
$$

$$
\eta = \frac {P _ {s} (\tau)}{T _ {s}} = \left\{ \begin{array}{l l} \frac {\bar {q} _ {k} \left(P _ {1} (\tau)\right) ^ {2}}{T _ {1}}, & K = 1, \\ \frac {\left(1 - \prod_ {k = 1} ^ {K} \left(1 - \bar {q} _ {k} P _ {k} (\tau)\right)\right) \left(1 - \prod_ {k = 1} ^ {K} \left(1 - P _ {k} (\tau)\right)\right)}{T _ {1} + \sum_ {k = 2} ^ {K} T _ {k} \prod_ {j = 1} ^ {k - 1} \left(1 - P _ {j} (\tau)\right)}, & K \geq 2. \end{array} \right. \tag {21}
$$

Proposition 2. The objective function η is unimodal with respect to the number of serving satellites K.

The proof of the Proposition 2 is given in Appendix F.

Given the above analysis and proof of unimodality, (P1) is still challenging to solve, since its objective function is derived from the stochastic-geometry analysis in Sections III-A and III-C and involves summations, products, and integrals, making it analytically intractable for conventional convex optimization methods. Furthermore, the decision variable, namely the number of serving satellites K, is integer-valued, and our objective is to find $K ^ { \star }$ under different network parameter settings. Therefore, directly applying continuous relaxation may yield non-integer solutions, which are not practically meaningful in the mLEO-CN. Since (P1) is a onedimensional integer optimization problem, tractable searchbased have been widely adopted in the existing studies on similar problems to efficiently obtain optimal solutions [13], [25], [38]–[40]. Motivated by these studies, we employ a one-dimensional search algorithm to solve (P1). Specifically, the core idea of the algorithm is to sequentially search over the number of serving satellites K for a given constellation altitude and terminate the search once η starts to decrease due to the unimodality of the objective function. The detailed steps are provided in Algorithm 1.

# IV. NUMERICAL RESULTS

# A. Parameter Settings

In the simulation, the GU is positioned on the Earth at a specific point $( 0 , 0 , r _ { \mathrm { e } } )$ with Earth radius $r _ { \mathrm { e } } = 6 3 7 1$ km. The N LEO satellite positions are created on a spherical layer at the altitude of $r _ { \mathrm { m i n } }$ above the Earth’s surface, constituting a BPP. All the LEO satellites are ranked from 1 to N according Algorithm 1 One-Dimensional Search Algorithm for Solving (P1)

Input: $\tau , \ r _ { \mathrm { m i n } } ,$ and upper bound on the number of serving satellites $K _ { \mathbf { u } }$

Output: maximum ratio of the overall transmission success probability to the end-to-end delay $\eta ^ { \star }$ and $K ^ { \star }$

1: Initialize $K \gets 1$ and compute η(1)   
2: for K from 2 to $K _ { \mathbf { u } }$ do   
3: Compute η(K) using (21)   
4: if $\eta ( K ) < \eta ( K - 1 )$ then   
5: Set $K ^ { \star } \gets K - 1$ and $\eta ^ { \star }  \eta ( K - 1 )$   
6: break   
7: end if   
8: end for   
9: if the search reaches $K _ { \mathrm { u } }$ without decrease then   
10: Set $K ^ { \star }  K _ { \mathrm { u } }$ and $\eta ^ { \star }  \eta ( K _ { \mathrm { u } } )$   
11: end if

to their distances to the GU. For simplicity, we set $q _ { 1 } = q _ { 2 } =$ $\ldots q _ { k } = q $ . Unless otherwise specified, N is set to 400, $r _ { \mathrm { m i n } }$ is set to 1000 km, the predefined SNR threshold τ is set to -10 dB, $r _ { 1 }$ as well as $r _ { \mathrm { u } }$ are set to 500 km and 1500 km, and $K _ { \mathrm { u } }$ is set to 10.

The transmit power of the GU is 3 W, and the transmit antenna gain and the receive antenna gain of the GU are set to 10 dBi and 0 dBi [38], respectively. For the LEO satellite, the transmit power is 10 W [7], the transmit antenna gain is set to 30 dBi, [38], and the receive antenna gain is set to 25 dBi [38]. The parameters in the SR fading model $( \boldsymbol { b } _ { \mathrm { s } } , m , \Omega )$ are set as (0.4, 3, 0.2) [27]. Moreover, the failure probability q is set to 0 or 0.1 to represent the two states of each LEO satellite. The noise power spectral densities (PSDs) $N _ { 0 }$ is set to −203 dBm/Hz [41]. The bandwidth of the channel in the space link is set as 250 MHz [42]. Therefore, by applying the relationship among noise PSD, bandwidth B, and noise power $\sigma ^ { 2 }$ , that is $N _ { 0 } B = \sigma ^ { 2 }$ [31], the noise power is −119 dBm. In addition, the path loss exponent α is set to 2.2, the carrier frequency $f _ { c }$ of the signal is set to 30 GHz and the handover delay $T _ { \mathrm { h o } }$ at each switch is set to 20 ms [43].

# B. Results and Discussion

In all the figures, the lines correspond to the analytical results, while the markers indicate the outcomes from Monte Carlo simulations. We verify the accuracy of our derivations for the overall transmission success probability and the corresponding asymptotic expressions derived in Sections III-A and B, as shown in Fig. 2 to Fig. 6. Fig. 2 illustrates how the overall transmission success probability varies with the predefined SNR threshold, comparing theoretical and simulation results under failure probabilities of $q { = } 0$ and $q { = } 0 . 1$ for $K { = } 1$ , 2, 3. Theoretical results match the simulations, validating the accuracy of the derivations. It is observable that increasing the number of cooperative LEO satellites leads to a gradual enhancement in the overall transmission success probability. This is due to the fact that when the first LEO satellite suffers from a lower coverage performance due to factors such as channel fading, the employed serial communication scheme promotes additional LEO satellites to provide overlapping coverage for the GU, which in turn reduces the likelihood of outage. Therefore, the serial communication with multiple LEO satellites can effectively improve the end-to-end signal transmission performance compared to a single satellitesupported system. Moreover, the potential satellite failures significantly degrade the overall transmission success probability, particularly in the single-satellite scenario. For example, when $K { = } 1$ and $q { = } 0 ,$ , the transmission success probability ranges from 1 to 0.908 as the SNR threshold varies from -30 dB to -20 dB, whereas with $q { = } 0 . 1$ , it drops from 0.8 to 0.726. This reduction arises from the lack of alternative satellites to mitigate the impact of failure on the serving satellite. In contrast, when the failure probability $q = 0 . 1$ , the transmission success probability is substantially higher in the cases with K=2 and $K { = } 3 .$ , compared to the single-satellite case with $K { = } 1$ . Thus, the serial communication with multiple LEO satellites effectively alleviates induced degradation, enhancing the reliability and robustness of LEO satellite communication networks.

Fig. 3 illustrates the effect of constellation altitude on the overall transmission success probability. As the constellation altitude increases, the overall transmission success probability declines progressively. This phenomenon arises due to the extended distance between the GU and each LEO satellite at higher altitudes, amplifying path loss in signal transmissions. Consequently, both the received SNR in the uplink and the downlink deteriorate, lowering the overall transmission success probability. It is important to highlight that a discrepancy between theoretical and simulation results is observed at lower constellation altitudes, particularly for K=2 and $K { = } 3$ . This discrepancy stems from the low degree of alignment between the employed PDF of the distance between the $k ^ { \mathrm { t h } }$ LEO satellite and the GU and the actual distance distribution in practice.

![](images/b6fe89b26ad9a176c7d5324050999105d8dffecf329b8795141d710f13404c3a.jpg)

<details>
<summary>line</summary>

| SNR threshold, τ (dB) | Theory K=1, q=0 | Simulation K=1, q=0 | Theory K=2, q=0 | Simulation K=2, q=0 | Theory K=3, q=0 | Simulation K=3, q=0 | Theory K=1, q=0.1 | Simulation K=1, q=0.1 | Theory K=2, q=0.1 | Simulation K=2, q=0.1 | Theory K=3, q=0.1 | Simulation K=3, q=0.1 |
| --------------------- | --------------- | ------------------- | --------------- | ------------------- | --------------- | ------------------- | ----------------- | --------------------- | ----------------- | --------------------- | ----------------- | --------------------- |
| -30                   | 1.0             | 1.0                 | 1.0             | 1.0                 | 1.0             | 1.0                 | 0.9               | 0.9                   | 0.9               | 0.9                   | 0.9               | 0.9                   |
| -25                   | 0.95            | 0.95                | 0.95            | 0.95                | 0.95            | 0.95                | 0.85              | 0.85                  | 0.85              | 0.85                  | 0.85              | 0.85                  |
| -20                   | 0.85            | 0.85                | 0.85            | 0.85                | 0.85            | 0.85                | 0.7               | 0.7                   | 0.7               | 0.7                   | 0.7               | 0.7                   |
| -15                   | 0.7             | 0.7                 | 0.7             | 0.7                 | 0.7             | 0.7                 | 0.5               | 0.5                   | 0.5               | 0.5                   | 0.5               | 0.5                   |
| -10                   | 0.5             | 0.5                 | 0.5             | 0.5                 | 0.5             | 0.5                 | 0.3               | 0.3                   | 0.3               | 0.3                   | 0.3               | 0.3                   |
| -5                    | 0.2             | 0.2                 | 0.2             | 0.2                 | 0.2             | 0.2                 | 0.1               | 0.1                   | 0.1               | 0.1                   | 0.1               | 0.1                   |
| 0                     | 0.0             | 0.0                 | 0.0             | 0.0                 | 0.0             | 0.0                 | 0.0               | 0.0                   | 0.0               | 0.0                   | 0.0               | 0.0                   |
| 5                     | 0.0             | 0.0                 | 0.0             | 0.0                 | 0.0             | 0.0                 | 0.0               | 0.0                   | 0.0               | 0.0                   | 0.0               | 0.0                   |
</details>

Fig. 2. Effect of predefined SNR threshold τ on the overall transmission success probability.

![](images/b2a389dcabaf8712ace9902baa07e9a65b9fb1dbaf569fd8b027a2f5ad147ef6.jpg)

<details>
<summary>line</summary>

| Constellation altitude, r_min (km) | Theory K=1, q=0 | Theory K=1, q=0.1 | Simulation K=1, q=0 | Simulation K=1, q=0.1 | Theory K=2, q=0 | Theory K=2, q=0.1 | Simulation K=2, q=0 | Simulation K=2, q=0.1 | Theory K=3, q=0 | Theory K=3, q=0.1 | Simulation K=3, q=0 |
| ---------------------------------- | --------------- | ----------------- | ------------------- | --------------------- | --------------- | ----------------- | ------------------- | --------------------- | --------------- | ----------------- | ------------------- |
| 500                                | 0.9             | 0.9               | 0.8                 | 0.8                   | 0.8             | 0.8               | 0.8                 | 0.8                   | 0.9             | 0.9               | 0.9                 |
| 600                                | 0.8             | 0.8               | 0.7                 | 0.7                   | 0.7             | 0.7               | 0.7                 | 0.7                   | 0.8             | 0.8               | 0.8                 |
| 700                                | 0.7             | 0.7               | 0.6                 | 0.6                   | 0.6             | 0.6               | 0.6                 | 0.6                   | 0.7             | 0.7               | 0.7                 |
| 800                                | 0.6             | 0.6               | 0.5                 | 0.5                   | 0.5             | 0.5               | 0.5                 | 0.5                   | 0.6             | 0.6               | 0.6                 |
| 900                                | 0.5             | 0.5               | 0.4                 | 0.4                   | 0.4             | 0.4               | 0.4                 | 0.4                   | 0.5             | 0.5               | 0.5                 |
| 1000                               | 0.4             | 0.4               | 0.3                 | 0.3                   | 0.3             | 0.3               | 0.3                 | 0.3                   | 0.4             | 0.4               | 0.4                 |
| 1100                               | 0.3             | 0.3               | 0.2                 | 0.2                   | 0.2             | 0.2               | 0.2                 | 0.2                   | 0.3             | 0.3               | 0.3                 |
| 1200                               | 0.2             | 0.2               | 0.1                 | 0.1                   | 0.1             | 0.1               | 0.1                 | 0.1                   | 0.2             | 0.2               | 0.2                 |
| 1300                               | 0.1             | 0.1               | 0.0                 | 0.0                   | 0.0             | 0.0               | 0.0                 | 0.0                   | 0.1             | 0.1               | 0.1                 |
| 1400                               | 0.0             | 0.0               | 0.0                 | 0.0                   | 0.0             | 0.0               | 0.0                 | 0.0                   | 0.0             | 0.0               | 0.0                 |
| 1500                               | 0.0             | 0.0               | 0.0                 | 0.0                   | 0.0             | 0.0               | 0.0                 | 0.0                   | 0.0             | 0.0               | 0.0                 |
</details>

Fig. 3. Effect of the constellation altitude on the overall transmission success probability.

Fig. 4 illustrates the relationship between the overall transmission success probability and the constellation size. As the constellation size increases from 100 to 600, a steady rise in the overall transmission success probability is observed. This improvement is attributed to the increased density of LEO satellites, which reduces the average distance between the GU and the serving LEO satellites. The shorter signal propagation distance enhances the quality of both uplink and downlink channels, bringing an improvement in the overall transmission success probability.

The validation of the derived asymptotic expressions for the overall transmission success probability in two scenarios is presented in Fig. 5. Fig. 5(a) illustrates the asymptotic expression for Case 1, where the predefined SNR threshold ranges from -30 dB to -20 dB, while Fig. 5(b) depicts the results for Case 2, considering a SNR threshold from -7 dB to 3 dB. The consistency between the analytical results and the simulation outcomes confirms the accuracy of the derived expressions. However, in Case 1, the asymptotic expression in (11) is valid only in the high-SNR regime, limiting its applicability across the entire SNR range. In contrast, for Case 2, results are provided within the SNR range of -7 dB to 3 dB. The results clearly demonstrate the validity of approximating the CDF of SR fading using the Gamma distribution.

![](images/f846060cfb73804d36d12318a96f4d2693847d02888468ff174a410645223eee.jpg)

<details>
<summary>line</summary>

| Constellation size, N | Theory K=1, q=0 | Theory K=1, q=0.1 | Simulation K=1, q=0 | Simulation K=1, q=0.1 | Theory K=2, q=0 | Theory K=2, q=0.1 | Simulation K=2, q=0 | Theory K=2, q=0.1 | Simulation K=2, q=0.1 | Theory K=3, q=0 | Theory K=3, q=0.1 | Simulation K=3, q=0 | Theory K=3, q=0.1 | Simulation K=3, q=0.1 |
| ---------------------- | --------------- | ----------------- | ------------------- | ---------------------- | --------------- | ----------------- | ------------------- | ----------------- | ---------------------- | --------------- | ----------------- | ------------------- | ----------------- | ------------------- |
| 100                    | 0.25            | 0.25              | 0.25                | 0.25                   | 0.30            | 0.30              | 0.30                | 0.30              | 0.30                   | 0.35            | 0.35              | 0.35                | 0.35              | 0.35                |
| 150                    | 0.30            | 0.30              | 0.30                | 0.30                   | 0.40            | 0.40              | 0.40                | 0.40              | 0.40                   | 0.45            | 0.45              | 0.45                | 0.45              | 0.45                |
| 200                    | 0.35            | 0.35              | 0.35                | 0.35                   | 0.45            | 0.45              | 0.45                | 0.45              | 0.45                   | 0.50            | 0.50              | 0.50                | 0.50              | 0.50                |
| 250                    | 0.40            | 0.40              | 0.40                | 0.40                   | 0.50            | 0.50              | 0.50                | 0.50              | 0.50                   | 0.55            | 0.55              | 0.55                | 0.55              | 0.55                |
| 300                    | 0.45            | 0.45              | 0.45                | 0.45                   | 0.55            | 0.55              | 0.55                | 0.55              | 0.55                   | 0.60            | 0.60              | 0.60                | 0.60              | 0.60                |
| 350                    | 0.50            | 0.50              | 0.50                | 0.50                   | 0.60            | 0.60              | 0.60                | 0.60              | 0.60                   | 0.65            | 0.65              | 0.65                | 0.65              | 0.65                |
| 400                    | 0.55            | 0.55              | 0.55                | 0.55                   | 0.65            | 0.65              | 0.65                | 0.65              | 0.65                   | 0.70            | 0.70              | 0.70                | 0.70              | 0.70                |
| 450                    | 0.60            | 0.60              | 0.60                | 0.60                   | 0.70            | 0.70              | 0.70                | 0.70              | 0.70                   | 0.75            | 0.75              | 0.75                | 0.75              | 0.75                |
| 500                    | 0.65            | 0.65              | 0.65                | 0.65                   | 0.75            | 0.75              | 0.75                | 0.75              | 0.75                   | 0.80            | 0.80              | 0.80                | 0.80              | 0.80                |
| 550                    | 0.70            | 0.70              | 0.70                | 0.70                   | 0.80            | 0.80              | 0.80                | 0.80              | 0.80                   | 0.85            | 0.85              | 0.85                | 0.85              | 0.85                |
| 600                    | 0.75            | 0.75              | 0.75                | 0.75                   | 0.85            | 0.85              | 0.85                | 0.85              | 0.85                   | 0.90            | 0.90              | 0.90                | 0.90              | 0.90                |
</details>

Fig. 4. Effect of the constellation size on the overall transmission success probability.

![](images/32dc9ad30ebcde098884e38c193c8176085abb2cce219387f7867b2c3b7847c7.jpg)

<details>
<summary>line</summary>

| The number of serving LEO satellites | Clu-App. r_min=1000 km, q=0 | Clu-App. r_min=1000 km, q=0.1 | Simulation r_min=1000 km, q=0 | Simulation r_min=1000 km, q=0.1 | Clu-App. r_min=1500 km, q=0 | Clu-App. r_min=1500 km, q=0.1 | Simulation r_min=1500 km, q=0 | Simulation r_min=1500 km, q=0.1 |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.4 | 0.4 | 0.37 | 0.37 | 0.15 | 0.15 | 0.15 | 0.15 |
| 2 | 0.55 | 0.55 | 0.52 | 0.52 | 0.23 | 0.23 | 0.23 | 0.23 |
| 3 | 0.65 | 0.65 | 0.61 | 0.61 | 0.29 | 0.29 | 0.29 | 0.29 |
| 4 | 0.7 | 0.7 | 0.66 | 0.66 | 0.34 | 0.34 | 0.34 | 0.34 |
| 5 | 0.73 | 0.73 | 0.69 | 0.69 | 0.37 | 0.37 | 0.37 | 0.37 |
| 6 | 0.75 | 0.75 | 0.71 | 0.71 | 0.38 | 0.38 | 0.38 | 0.38 |
| 7 | 0.76 | 0.76 | 0.72 | 0.72 | 0.39 | 0.39 | 0.39 | 0.39 |
| 8 | 0.77 | 0.77 | 0.73 | 0.73 | 0.39 | 0.39 | 0.39 | 0.39 |
| 9 | 0.78 | 0.78 | 0.74 | 0.74 | 0.4 | 0.4 | 0.4 | 0.4 |
</details>

Fig. 6. Validation of the proposed cluster-based approximation approach on the overall transmission success probability with K=3.

![](images/7bd0323e0720b40b93c4add2ef533716908720e15b50d845c2b9a45ab8271d45.jpg)

<details>
<summary>line</summary>

| SNR threshold, τ (dB) | High SNR K=1, q=0.1 | High SNR K=1, q=0.1 | High SNR K=2, q=0.1 | High SNR K=2, q=0.1 | High SNR K=3, q=0.1 | High SNR K=3, q=0.1 |
| --------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- |
| -30                   | 1.0                 | 1.0                 | 1.0                 | 1.0                 | 1.0                 | 1.0                 |
| -29                   | 0.98                | 0.98                | 0.98                | 0.98                | 0.98                | 0.98                |
| -28                   | 0.96                | 0.96                | 0.96                | 0.96                | 0.96                | 0.96                |
| -27                   | 0.94                | 0.94                | 0.94                | 0.94                | 0.94                | 0.94                |
| -26                   | 0.92                | 0.92                | 0.92                | 0.92                | 0.92                | 0.92                |
| -25                   | 0.90                | 0.90                | 0.90                | 0.90                | 0.90                | 0.90                |
| -24                   | 0.88                | 0.88                | 0.88                | 0.88                | 0.88                | 0.88                |
| -23                   | 0.86                | 0.86                | 0.86                | 0.86                | 0.86                | 0.86                |
| -22                   | 0.84                | 0.84                | 0.84                | 0.84                | 0.84                | 0.84                |
| -21                   | 0.82                | 0.82                | 0.82                | 0.82                | 0.82                | 0.82                |
| -20                   | 0.80                | 0.80                | 0.80                | 0.80                | 0.80                | 0.80                |
</details>

![](images/2010de9b73568238959a97af57b15c3257efcecaae4f8fe92e65429709d10198.jpg)

<details>
<summary>line</summary>

(b) SNR threshold, τ (dB)
| SNR threshold, τ (dB) | Gamm-app. K=1, q=0 | Simulation K=1, q=0 | Gamm-app. K=2, q=0 | Simulation K=2, q=0 | Gamm-app. K=3, q=0 | Simulation K=3, q=0 |
|---|---|---|---|---|---|---|
| -7 | 0.3 | 0.25 | 0.2 | 0.18 | 0.28 | 0.22 |
| -6 | 0.25 | 0.2 | 0.18 | 0.15 | 0.22 | 0.18 |
| -5 | 0.2 | 0.15 | 0.12 | 0.1 | 0.18 | 0.14 |
| -4 | 0.12 | 0.1 | 0.08 | 0.07 | 0.12 | 0.09 |
| -3 | 0.06 | 0.05 | 0.04 | 0.03 | 0.06 | 0.04 |
| -2 | 0.03 | 0.03 | 0.02 | 0.02 | 0.03 | 0.02 |
| -1 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 |
| 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
</details>

Fig. 5. Validation of asymptotic expressions on the end-to-end transmission success probability through the $k ^ { \mathrm { t h } }$ LEO satellite under two special cases.

![](images/dc485f6b60ff36770fb82db61170178abf2043a76bdad5122f7f202e2023ba1f.jpg)

<details>
<summary>line</summary>

| Constellation altitude, r_min (km) | Theory, K=1, q=0 | Theory, K=1, q=0.1 | Simulation, K=1, q=0 | Simulation, K=1, q=0.1 | Theory, K=2, q=0 | Theory, K=2, q=0.1 | Simulation, K=2, q=0 | Simulation, K=2, q=0.1 | Theory, K=3, q=0 | Theory, K=3, q=0.1 | Simulation, K=3, q=0.1 |
| ---------------------------------- | ---------------- | ------------------ | --------------------- | ----------------------- | ---------------- | ------------------ | --------------------- | ----------------------- | ---------------- | ------------------ | ----------------------- |
| 500                                | 10.5e7           | 10.5e7             | 8.5e7                 | 8.5e7                   | 10.0e7           | 10.0e7             | 9.5e7                 | 9.5e7                   | 10.5e7           | 10.5e7             | 10.5e7                  |
| 600                                | 9.5e7            | 9.5e7              | 7.5e7                 | 7.5e7                   | 9.0e7            | 9.0e7              | 8.5e7                 | 8.5e7                   | 9.5e7            | 9.5e7              | 9.5e7                   |
| 700                                | 8.5e7            | 8.5e7              | 6.5e7                 | 6.5e7                   | 8.0e7            | 8.0e7              | 7.5e7                 | 7.5e7                   | 8.5e7            | 8.5e7              | 8.5e7                   |
| 800                                | 7.5e7            | 7.5e7              | 5.5e7                 | 5.5e7                   | 7.0e7            | 7.0e7              | 6.5e7                 | 6.5e7                   | 7.5e7            | 7.5e7              | 7.5e7                   |
| 900                                | 6.5e7            | 6.5e7              | 4.5e7                 | 4.5e7                   | 6.0e7            | 6.0e7              | 5.5e7                 | 5.5e7                   | 6.5e7            | 6.5e7              | 6.5e7                   |
| 1000                               | 5.5e7            | 5.5e7              | 3.5e7                 | 3.5e7                   | 5.0e7            | 5.0e7              | 4.5e7                 | 4.5e7                   | 5.5e7            | 5.5e7              | 5.5e7                   |
| 1100                               | 4.5e7            | 4.5e7              | 2.5e7                 | 2.5e7                   | 4.0e7            | 4.0e7              | 3.5e7                 | 3.5e7                   | 4.5e7            | 4.5e7              | 4.5e7                   |
| 1200                               | 3.5e7            | 3.5e7              | 1.5e7                 | 1.5e7                   | 3.0e7            | 3.0e7              | 2.5e7                 | 2.5e7                   | 3.5e7            | 3.5e7              | 3.5e7                   |
| 1300                               | 2.5e7            | 2.5e7              | 0.5e7                 | 0.5e7                   | 2.0e7            | 2.0e7              | 1.5e7                 | 1.5e7                   | 2.5e7            | 2.5e7              | 2.5e7                   |
| 1400                               | 1.5e7            | 1.5e7              | 0.0e7                 | 0.0e7                   | 1.0e7            | 1.0e7              | 0.5e7                 | 0.5e7                   | 1.5e7            | 1.5e7              | 1.5e7                   |
| 1500                               | 0.5e7            | 0.5e7              | 0.0e7                 | 0.0e7                   | 0.5e7            | 0.5e7              | 0.0e7                 | 0.0e7                   | 0.5e7            | 0.5e7              | 0.5e7                   |
</details>

Fig. 7. Effect of the constellation altitude on the average transmission rate capacity.

The validation of the proposed cluster-based approximation approach with K=3 is presented in Fig. 6. The close alignment between the approximated and simulated results confirms the effectiveness and accuracy of the proposed approach. Furthermore, as the number of serving LEO satellites increases, the overall transmission success probability exhibits a rising trend before gradually stabilizing. This observation suggests that while more serving LEO satellites enhance the coverage performance of the LEO satellite communication network, the enhancement is bounded and does not yield unlimited gains.

Our derivations of the average transmission rate capacity are validated through Monte Carlo simulations, with results presented in Figs. 7 and 8. Specifically, they illustrate how the average transmission rate capacity varies with the constellation altitude and the constellation size, respectively. The results indicate that an increase in constellation altitude leads to a reduction in the average transmission rate capacity. In contrast, as the constellation size grows from 100 to 600, there is a gradual improvement in the average transmission rate capacity. Furthermore, the adoption of the serial communication scheme, e.g., K=2 and K=3, results in a notable enhancement in the average transmission rate capacity as compared to the single-satellite scenario with K=1.

The validation of the end-to-end delay expressions derived in Theorem 3 is presented in Figs. 9 and 10. Fig. 9 illustrates the impact of constellation altitude on the end-to-end delay when packet length ω is 0.1 Mbits and 1 Mbits, respectively. It can be seen that as the constellation altitude increases, the end-to-end delay exhibits an upward trend. This is attributed to higher constellation altitudes increasing the distance between LEO satellites and the GU, thereby resulting in longer transmission delays. Furthermore, the end-to-end delay increases with the number of serving LEO satellites due to the additional handover delay introduced in mLEO-CN. The variation of endto-end delay with respect to the constellation size is depicted in Fig. 10. It can be observed that the end-to-end delay decreases slightly as the constellation size increases from 100 to 500.

![](images/fc015b4a1a6a351ca89daaadcabc8f2738bf2a7679dc4516ec58b85d92e36515.jpg)

<details>
<summary>line</summary>

| Constellation size, N | Theory K=1, q=0 | Theory K=1, q=0.1 | Simulation K=1, q=0 | Simulation K=1, q=0.1 | Theory K=2, q=0 | Theory K=2, q=0.1 | Simulation K=2, q=0 | Simulation K=2, q=0.1 | Theory K=3, q=0 | Theory K=3, q=0.1 | Simulation K=3, q=0 | Theory K=3, q=0.1 | Simulation K=3, q=0.1 |
| ---------------------- | --------------- | ----------------- | ------------------- | --------------------- | --------------- | ----------------- | ------------------- | --------------------- | --------------- | ----------------- | ------------------- | ----------------- | --------------------- |
| 100                    | 1.5e7           | 1.5e7             | 1.5e7               | 1.5e7                 | 1.5e7           | 1.5e7             | 1.5e7               | 1.5e7                 | 1.5e7           | 1.5e7             | 1.5e7               | 1.5e7             | 1.5e7                 |
| 150                    | 2.0e7           | 2.0e7             | 2.0e7               | 2.0e7                 | 2.0e7           | 2.0e7             | 2.0e7               | 2.0e7                 | 2.0e7           | 2.0e7             | 2.0e7               | 2.0e7             | 2.0e7                 |
| 200                    | 2.5e7           | 2.5e7             | 2.5e7               | 2.5e7                 | 2.5e7           | 2.5e7             | 2.5e7               | 2.5e7                 | 2.5e7           | 2.5e7             | 2.5e7               | 2.5e7             | 2.5e7                 |
| 250                    | 3.0e7           | 3.0e7             | 3.0e7               | 3.0e7                 | 3.0e7           | 3.0e7             | 3.0e7               | 3.0e7                 | 3.0e7           | 3.0e7             | 3.0e7               | 3.0e7             | 3.0e7                 |
| 300                    | 3.5e7           | 3.5e7             | 3.5e7               | 3.5e7                 | 3.5e7           | 3.5e7             | 3.5e7               | 3.5e7                 | 3.5e7           | 3.5e7             | 3.5e7               | 3.5e7             | 3.5e7                 |
| 350                    | 4.0e7           | 4.0e7             | 4.0e7               | 4.0e7                 | 4.0e7           | 4.0e7             | 4.0e7               | 4.0e7                 | 4.0e7           | 4.0e7             | 4.0e7               | 4.0e7             | 4.0e7                 |
| 400                    | 4.5e7           | 4.5e7             | 4.5e7               | 4.5e7                 | 4.5e7           | 4.5e7             | 4.5e7               | 4.5e7                 | 4.5e7           | 4.5e7             | 4.5e7               | 4.5e7             | 4.5e7                 |
| 450                    | 5.0e7           | 5.0e7             | 5.0e7               | 5.0e7                 | 5.0e7           | 5.0e7             | 5.0e7               | 5.0e7                 | 5.0e7           | 5.0e7             | 5.0e7               | 5.0e7             | 5.0e7                 |
| 500                    | 5.5e7           | 5.5e7             | 5.5e7               | 5.5e7                 | 5.5e7           | 5.5e7             | 5.5e7               | 5.5e7                 | 5.5e7           | 5.5e7             | 5.5e7               | 5.5e7             | 5.5e7                 |
| 550                    | 6.0e7           | 6.0e7             | 6.0e7               | 6.0e7                 | 6.0e7           | 6.0e7             | 6.0e7               | 6.0e7                 | 6.0e7           | 6.0e7             | 6.0e7               | 6.0e7             | 6.0e7                 |
| 600                    | 6.5e7           | 6.5e7             | 6.5e7               | 6.5e7                 | 6.5e7           | 6.5e7             | 6.5e7               | 6.5e7                 | 6.5e7           | 6.5e7             | 6.5e7               | 6.5e7             | 6.5e7                 |
</details>

Fig. 8. Effect of the constellation size on the average transmission rate capacity.

![](images/99fd72431653924cbbabe0eea36b5939e711940a2ada5b760c24c23cf65eb305.jpg)

<details>
<summary>line</summary>

| Constellation altitude, r_min (km) | Theory, K=1, ω=0.1 Mbits | Theory, K=1, ω=1 Mbits | Simulation, K=1, ω=0.1 Mbits | Simulation, K=1, ω=1 Mbits | Theory, K=2, ω=0.1 Mbits | Theory, K=2, ω=1 Mbits | Simulation, K=2, ω=0.1 Mbits | Simulation, K=2, ω=1 Mbits | Theory, K=3, ω=0.1 Mbits | Theory, K=3, ω=1 Mbits | Simulation, K=3, ω=0.1 Mbits |
| ---------------------------------- | ------------------------ | ---------------------- | ----------------------------- | --------------------------- | ------------------------ | ---------------------- | ----------------------------- | --------------------------- | ------------------------ | ---------------------- | ----------------------------- |
| 500                                | 0.005                    | 0.005                  | 0.005                         | 0.005                       | 0.005                    | 0.005                  | 0.005                         | 0.005                       | 0.005                    | 0.005                  | 0.005                         |
| 600                                | 0.006                    | 0.006                  | 0.006                         | 0.006                       | 0.006                    | 0.006                  | 0.006                         | 0.006                       | 0.006                    | 0.006                  | 0.006                         |
| 700                                | 0.007                    | 0.007                  | 0.007                         | 0.007                       | 0.007                    | 0.007                  | 0.007                         | 0.007                       | 0.007                    | 0.007                  | 0.007                         |
| 800                                | 0.008                    | 0.008                  | 0.008                         | 0.008                       | 0.008                    | 0.008                  | 0.008                         | 0.008                       | 0.008                    | 0.008                  | 0.008                         |
| 900                                | 0.009                    | 0.009                  | 0.009                         | 0.009                       | 0.009                    | 0.009                  | 0.009                         | 0.009                       | 0.009                    | 0.009                  | 0.009                         |
| 1000                               | 0.010                    | 0.010                  | 0.010                         | 0.010                       | 0.010                    | 0.010                  | 0.010                         | 0.010                       | 0.010                    | 0.010                  | 0.010                         |
| 1100                               | 0.011                    | 0.011                  | 0.011                         | 0.011                       | 0.011                    | 0.011                  | 0.011                         | 0.011                       | 0.011                    | 0.011                  | 0.011                         |
| 1200                               | 0.012                    | 0.012                  | 0.012                         | 0.012                       | 0.012                    | 0.012                  | 0.012                         | 0.012                       | 0.012                    | 0.012                  | 0.012                         |
| 1300                               | 0.013                    | 0.013                  | 0.013                         | 0.013                       | 0.013                    | 0.013                  | 0.013                         | 0.013                       | 0.013                    | 0.013                  | 0.013                         |
| 1400                               | 0.014                    | 0.014                  | 0.014                         | 0.014                       | 0.014                    | 0.014                  | 0.014                         | 0.014                       | 0.014                    | 0.014                  | 0.014                         |
| 1500                               | 0.015                    | 0.015                  | 0.015                         | 0.015                       | 0.015                    | 0.015                  | 0.015                         | 0.015                       | 0.015                    | 0.015                  | 0.015                         |
</details>

Fig. 9. Effect of the constellation altitude on the end-to-end delay when packet length ω is 0.1 Mbits and 1 Mbits.

This phenomenon arises because with a higher satellite density, the serving satellite in each Monte Carlo realization is more likely to be closer to the GU, thereby shortening the distance between the GU and the serving satellites, and then reducing the uplink and downlink transmission delays through the $k ^ { \mathrm { t h } }$ LEO satellite. Consequently, the end-to-end delay decreases. However, when the constellation size is relatively small, a discrepancy exists between the theoretical and simulated values of the PDF describing the distance between an LEO satellite and the GU. This discrepancy results in a deviation in the end-to-end delay.

Fig. 11 demonstrates the maximum ratio η and the optimal number of serving LEO satellites at different constellation altitudes. It is obvious that when the constellation altitude is high, the overall transmission success probability of a single satellite decreases, necessitating a larger number of serving LEO satellites to enhance the overall performance of the mLEO-CN. Conversely, at lower altitudes, a single satellite provides sufficient coverage, making it preferable to reduce the number of serving satellites to reduce the endto-end delay. For large packet transmissions, the end-to-end delay is primarily determined by transmission delay, with handover delay being negligible. Thus, increasing the number of serving LEO satellites is recommended to enhance network reliability. In contrast, the increased transmission delay makes serial communication supported by multiple LEO satellites less attractive, as frequent switches can degrade network performance despite improving the overall transmission success probability.

![](images/28b7c278aed142ed36d0950a70b29482e21f204eb7a09167cf9da9da36a2686c.jpg)

<details>
<summary>line</summary>

| Constellation size, N | Theory K=1, ω=0.1 Mbits | Simulation K=1, ω=0.1 Mbits | Theory K=2, ω=0.1 Mbits | Simulation K=2, ω=0.1 Mbits | Theory K=3, ω=0.1 Mbits | Simulation K=3, ω=0.1 Mbits |
| --------------------- | ------------------------ | ---------------------------- | ------------------------ | ---------------------------- | ------------------------ | ---------------------------- |
| 100                   | 0.004                    | 0.008                        | 0.030                    | 0.035                        | 0.010                    | 0.038                        |
| 150                   | 0.004                    | 0.008                        | 0.029                    | 0.035                        | 0.011                    | 0.039                        |
| 200                   | 0.004                    | 0.008                        | 0.028                    | 0.035                        | 0.012                    | 0.039                        |
| 250                   | 0.004                    | 0.008                        | 0.028                    | 0.035                        | 0.013                    | 0.039                        |
| 300                   | 0.004                    | 0.008                        | 0.027                    | 0.035                        | 0.013                    | 0.039                        |
| 350                   | 0.004                    | 0.008                        | 0.027                    | 0.035                        | 0.013                    | 0.039                        |
| 400                   | 0.004                    | 0.008                        | 0.027                    | 0.035                        | 0.013                    | 0.039                        |
| 450                   | 0.004                    | 0.008                        | 0.027                    | 0.035                        | 0.013                    | 0.039                        |
| 500                   | 0.004                    | 0.008                        | 0.027                    | 0.035                        | 0.013                    | 0.039                        |
</details>

Fig. 10. Effect of the constellation size on the end-to-end delay when packet length ω is 0.1 Mbits and 1 Mbits.

![](images/f96e1bf36d41b32a2a429969a253aacd90db45a21cef1c2dd6ff68de196c836d.jpg)

<details>
<summary>line</summary>

| Constellation altitude, r_min (km) | ω=0.1 Mbits | ω=1 Mbit | ω=10 Mbit |
| ---------------------------------- | ----------- | -------- | --------- |
| 500                                | 400         | 50       | 0         |
| 600                                | 350         | 45       | 0         |
| 700                                | 300         | 40       | 0         |
| 800                                | 250         | 35       | 0         |
| 900                                | 200         | 30       | 0         |
| 1000                               | 150         | 25       | 0         |
| 1100                               | 100         | 20       | 0         |
| 1200                               | 75          | 15       | 0         |
| 1300                               | 50          | 10       | 0         |
| 1400                               | 25          | 5        | 0         |
| 1500                               | 0           | 0        | 0         |
</details>

![](images/9324d7f6a39e4d9f07a011c77da19d9578e4b6dd1abeb6666b92eccbe884ab3e.jpg)

<details>
<summary>bar</summary>

(b) Constellation altitude, r_min (km) | ω=0.1 Mbits | ω=1 Mbits | ω=10 Mbits |
|---|---|---|---|
| 500 | 1.0 | 1.0 | 2.0 |
| 600 | 1.0 | 1.0 | 3.0 |
| 700 | 1.0 | 1.0 | 3.0 |
| 800 | 1.0 | 1.0 | 3.0 |
| 900 | 1.0 | 1.0 | 4.0 |
| 1000 | 1.0 | 2.0 | 4.0 |
| 1100 | 1.0 | 2.0 | 5.0 |
| 1200 | 1.0 | 2.0 | 5.0 |
| 1300 | 1.0 | 2.0 | 6.0 |
| 1400 | 1.0 | 2.0 | 6.0 |
| 1500 | 1.0 | 3.0 | 6.0 |
</details>

Fig. 11. Optimal number of LEO satellites and maximum overall transmission success probability vary with different constellation altitudes.

# V. CONCLUSION

In this paper, we have considered an mLEO-CN where the typical GU is served by multiple LEO satellites serially and developed a theoretical framework to assess its key performance metrics, leveraging the tool of stochastic geometry. The metrics include overall transmission success probability, average transmission rate capacity, and end-to-end delay. To simplify the analytical complexity, we have further derived the asymptotic transmission success probability and proposed a cluster-based approximation for simplification. Based on these analytical results, we have formulated and solved an optimization problem to determine the optimal number of serving satellites that maximizes the trade-off between transmission reliability and latency. Extensive numerical results are presented to evaluate the impact of the key parameters on the end-to-end transmission performance. For the potential followup research, first, a key direction is to derive more tractable PDFs of the distance between each LEO satellite and the GU under various spatial distributions, such as PPP and BPP, thereby facilitating more precise system-level performance analysis in scenarios involving multiple satellites. Another important direction is to investigate the network performance of the mLEO-CN under severe co-channel interference, as this would further extend the present analytical framework to more spectrum-reuse-intensive and interference-limited scenarios.

# APPENDIX

# A. Proof of Theorem 1

To obtain (9), we derive from the definition of the endto-end transmission success probability through the $k ^ { \mathrm { t h } }$ LEO satellite, which is expressed as

$$
P _ {k} (\tau) \triangleq \mathbb {P} \left(\mathrm{SNR} _ {k} ^ {\mathrm{u}} > \tau , \mathrm{SNR} _ {k} ^ {\mathrm{d}} > \tau\right)
$$

$$
= \mathbb {P} \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} L _ {k} (R _ {k}) \left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}}{\sigma_ {k} ^ {2}} > \tau , \frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} L _ {k} (R _ {k}) \left| H _ {k} ^ {\mathrm{d}} \right| ^ {2}}{\sigma_ {k} ^ {2}} > \tau\right)
$$

$$
\underline {{\underline {{(a)}}}} \mathbb {P} \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} L _ {k} \left(R _ {k}\right) \left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}}{\sigma_ {k} ^ {2}} > \tau\right)
$$

$$
\times \mathbb {P} \left(\frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} L _ {k} (R _ {k}) | H _ {k} ^ {\mathrm{d}} | ^ {2}}{\sigma_ {k} ^ {2}} > \tau\right)
$$

$$
= \mathbb {P} \left(\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2} > \frac {\tau \mathcal {G} R _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right) \mathbb {P} \left(\left| H _ {k} ^ {\mathrm{d}} \right| ^ {2} > \frac {\tau \mathcal {G} R _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right)
$$

$$
\underline {{\underline {{(b)}}}} \overline {{F}} _ {\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}} \left(\frac {\tau \mathcal {G} R _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right) \overline {{F}} _ {\left| H _ {k} ^ {\mathrm{d}} \right| ^ {2}} \left(\frac {\tau \mathcal {G} R _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right)
$$

$$
\underline {{\underline {{(c)}}}} \int_ {r _ {\min}} ^ {r _ {\max}} \overline {{F}} _ {\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}} \left(\frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right) \overline {{F}} _ {\left| H _ {k} ^ {\mathrm{d}} \right| ^ {2}} \left(\frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right) f _ {R _ {k}} \left(r _ {k}\right) d r _ {k}. \tag {23}
$$

where (a) is obtained from the independence of the uplink and downlink in the $k ^ { \mathrm { t h } }$ channel, (b) employs the complementary CDF (CCDF) of the channel fading gain, and (c) is obtained using the PDF of the distance in Lemma 1. Then, by substituting the expression for the CDF of the SR fading model from step (c), (9) is obtained. □

# B. Proof of Corollary 1

To obtain (11), we continue to derive the expression from the last line of (23), given as

$$
P _ {k} ^ {\infty} (\tau)
$$

$$
= \int_ {r _ {\min}} ^ {r _ {\max}} \overline {{F}} _ {\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}} ^ {\infty} \left(\frac {\tau G r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right) \overline {{F}} _ {\left| H _ {k} ^ {\mathrm{d}} \right| ^ {2}} ^ {\infty} \left(\frac {\tau G r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right) f _ {R _ {k}} \left(r _ {k}\right) d r _ {k}
$$

$$
= \int_ {r _ {\min}} ^ {r _ {\max}} \left(1 - F _ {\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}} ^ {\infty} \left(\frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right)\right) \left(1 - F _ {\left| H _ {k} ^ {\mathrm{d}} \right| ^ {2}} ^ {\infty} \left(\frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right)\right)
$$

$$
\times f _ {R _ {k}} \left(r _ {k}\right) d r _ {k}
$$

$$
\stackrel {(a)} {\approx} \int_ {r _ {\min}} ^ {r _ {\max}} \left(1 - \frac {\mu \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right) \left(1 - \frac {\mu \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right) f _ {R _ {k}} (r _ {k}) d r _ {k}
$$

$$
= \int_ {r _ {\min}} ^ {r _ {\max}} \left(1 + \frac {\mu \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}} \frac {\mu \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}} - \frac {\mu \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}} - \frac {\mu \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right) \tag {24}
$$

$$
\times f _ {R _ {k}} \left(r _ {k}\right) d r _ {k},
$$

where (a) is obtained by employing the approximated CDF of SR fading at high SNR regime in (10). Due to the linear combination of the four items, the expression is expanded as

$$
\int_ {r _ {\min}} ^ {r _ {\max}} f _ {R _ {k}} (r _ {k}) d r _ {k} + \int_ {r _ {\min}} ^ {r _ {\max}} \frac {\mu \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}} \frac {\mu \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}} f _ {R _ {k}} (r _ {k}) d r _ {k}
$$

$$
- \int_ {r _ {\min}} ^ {r _ {\max}} \frac {\mu \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}} f _ {R _ {k}} \left(r _ {k}\right) d r _ {k} - \int_ {r _ {\min}} ^ {r _ {\max}} \frac {\mu \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}} f _ {R _ {k}} \left(r _ {k}\right) d r _ {k}. \tag {25}
$$

Based on the property that the integral of the PDF over its entire domain equals one, the first item can be calculated. For the rest of the three items, due to the similarity in the derivation steps, we take the second item as an example to begin the derivation, which is expressed as

$$
\int_ {r _ {\min}} ^ {r _ {\max}} \frac {\mu \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}} \frac {\mu \tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}} f _ {R _ {k}} (r _ {k}) d r _ {k}
$$

$$
= \frac {\mu^ {2} \tau^ {2} \mathcal {G} ^ {2}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \Xi} \int_ {r _ {\min}} ^ {r _ {\max}} r _ {k} ^ {2 \alpha} \sum_ {l = 0} ^ {k - 1} \sum_ {n = 0} ^ {N - k} \frac {\psi}{\Theta} r _ {k} ^ {2 n + 2 l + 1} d r _ {k}
$$

$$
= \frac {\mu^ {2} \tau^ {2} \mathcal {G} ^ {2}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \Xi} \sum_ {l = 0} ^ {k - 1} \sum_ {n = 0} ^ {N - k} \frac {\psi}{\Theta} \int_ {r _ {\min}} ^ {r _ {\max}} r _ {k} ^ {2 \alpha + 2 n + 2 l + 1} d r _ {k} \tag {26}
$$

$$
= \frac {\mu^ {2} \tau^ {2} \mathcal {G} ^ {2}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \Xi} \sum_ {l = 0} ^ {k - 1} \sum_ {n = 0} ^ {N - k} \frac {\psi}{\Theta} \left(\frac {r _ {\max} ^ {2 \alpha + \Delta} - r _ {\min} ^ {2 \alpha + \Delta}}{2 \alpha + \Delta}\right).
$$

Following similar steps, we can derive similar closed-form expressions for other items, and then (11) is obtained. □

# C. Proof of Corollary 2

To obtain (13), we start from the last line of (23), given as

$$
P _ {k} (\tau) \triangleq \mathbb {P} \left(\mathrm{SNR} _ {k} ^ {\mathrm{u}} > \tau , \mathrm{SNR} _ {k} ^ {\mathrm{d}} > \tau\right)
$$

$$
= \mathbb {P} \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} L _ {k} (R _ {k}) | H _ {k} ^ {\mathrm{u}} | ^ {2}}{\sigma_ {k} ^ {2}} > \tau , \frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} L _ {k} (R _ {k}) | H _ {k} ^ {\mathrm{d}} | ^ {2}}{\sigma_ {k} ^ {2}} > \tau\right)
$$

$$
\stackrel {(a)} {\approx} \int_ {r _ {\min}} ^ {r _ {\max}} \left(1 - \frac {\gamma \left(\alpha_ {s} , \frac {1}{\beta_ {s}} \frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right)}{\Gamma \left(\alpha_ {s}\right)}\right) \left(1 - \frac {\gamma \left(\alpha_ {s} , \frac {1}{\beta_ {s}} \frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right)}{\Gamma \left(\alpha_ {s}\right)}\right)
$$

$$
\times f _ {R _ {k}} \left(r _ {k}\right) d r _ {k}
$$

$$
\stackrel {(b)} {=} \int_ {r _ {\min}} ^ {r _ {\max}} \frac {\Gamma \left(\alpha_ {s} , \frac {1}{\beta_ {s}} \frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right)}{\Gamma \left(\alpha_ {s}\right)} \frac {\Gamma \left(\alpha_ {s} , \frac {1}{\beta_ {s}} \frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right)}{\Gamma \left(\alpha_ {s}\right)} f _ {R _ {k}} \left(r _ {k}\right) d r _ {k}
$$

$$
\underline {{\underline {{(c)}}}} \int_ {r _ {\min}} ^ {r _ {\max}} \exp \left(- \frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right) \sum_ {t _ {1} = 0} ^ {\widetilde {\alpha_ {s}} - 1} \frac {\left(\frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right) ^ {t _ {1}}}{\Gamma (t _ {1} + 1)}
$$

$$
\times \exp \left(- \frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right) \sum_ {t _ {2} = 0} ^ {\widetilde {\alpha_ {s}} - 1} \frac {\left(\frac {\tau \mathcal {G} r _ {k} ^ {\alpha}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right) ^ {t _ {2}}}{\Gamma (t _ {2} + 1)} f _ {R _ {k}} (r _ {k}) d r _ {k}
$$

$$
= \frac {1}{\Xi} \sum_ {l = 0} ^ {k - 1} \sum_ {n = 0} ^ {N - k} \sum_ {t _ {1} = 0} ^ {\widetilde {\alpha_ {s}} - 1} \sum_ {t _ {2} = 0} ^ {\widetilde {\alpha_ {s}} - 1} \frac {\psi}{\Theta} \frac {\left(\frac {\tau \mathcal {G}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right) ^ {t _ {1}} \left(\frac {\tau \mathcal {G}}{p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}}}\right) ^ {t _ {2}}}{\Gamma (t _ {1} + 1) \Gamma (t _ {2} + 1)}
$$

$$
\begin{array}{l} C _ {k} \triangleq B \log_ {2} \left(1 + \min \left(\mathrm{SNR} _ {k} ^ {\mathrm{u}}, \mathrm{SNR} _ {k} ^ {\mathrm{d}}\right) \mid \left(\mathrm{SNR} _ {k} ^ {\mathrm{u}} > \tau , \mathrm{SNR} _ {k} ^ {\mathrm{u}} > \tau\right)\right) \\ = B \log_ {2} \left(1 + \min \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| H _ {k} ^ {\mathrm{u}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}}, \frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| H _ {k} ^ {\mathrm{d}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}}\right) \mid \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| H _ {k} ^ {\mathrm{u}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau , \frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| H _ {k} ^ {\mathrm{d}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right)\right) \\ \underline {{\underline {{(a)}}}} B \mathrm{log} _ {2} \left(1 + \min \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} | H _ {k} ^ {\mathrm{u}} | ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}}, \frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} | H _ {k} ^ {\mathrm{d}} | ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}}\right)\right) \mathbb {1} \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} | H _ {k} ^ {\mathrm{u}} | ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) \mathbb {1} \left(\frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} | H _ {k} ^ {\mathrm{d}} | ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) \\ \underline {{\underline {{(b)}}}} B \int_ {0} ^ {\infty} \int_ {0} ^ {\infty} \log_ {2} \left(1 + \min \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| h _ {k} ^ {\mathrm{u}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}}, \frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| h _ {k} ^ {\mathrm{d}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}}\right)\right) \mathbb {1} \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| h _ {k} ^ {\mathrm{u}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) \mathbb {1} \left(\frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| h _ {k} ^ {\mathrm{d}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) \\ \times f _ {\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{u}}\right) f _ {\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{d}}\right) d h _ {k} ^ {\mathrm{u}} d h _ {k} ^ {\mathrm{d}} \\ \underline {{\underline {{(c)}}}} B \int_ {r _ {\min}} ^ {r _ {\max}} \int_ {0} ^ {\infty} \int_ {0} ^ {\infty} \log_ {2} \left(1 + \min \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| h _ {k} ^ {\mathrm{u}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}}, \frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| h _ {k} ^ {\mathrm{d}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}}\right)\right) \mathbb {1} \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| h _ {k} ^ {\mathrm{u}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) \\ \times \mathbb {1} \left(\frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| h _ {k} ^ {\mathrm{d}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) f _ {\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{u}}\right) f _ {\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{d}}\right) d h _ {k} ^ {\mathrm{u}} d h _ {k} ^ {\mathrm{d}} f _ {R _ {k}} \left(r _ {k}\right) d r _ {k}. \tag {28} \\ \end{array}
$$

$$
\times \int_ {r _ {\min}} ^ {r _ {\max}} r _ {k} ^ {(t _ {1} + t _ {2}) \alpha + 2 n + 2 l + 1} \exp (- \mathrm{A} r _ {k} ^ {\alpha}) d r _ {k}
$$

$$
= \frac {1}{\Xi} \sum_ {l = 0} ^ {k - 1} \sum_ {n = 0} ^ {N - k} \sum_ {t _ {1} = 0} ^ {\widetilde {\alpha_ {s}} - 1} \sum_ {t _ {2} = 0} ^ {\widetilde {\alpha_ {s}} - 1} \frac {\psi}{\Theta} \frac {\left(\frac {\tau \mathcal {G}}{p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}}}\right) ^ {t _ {1}} \left(\frac {\tau \mathcal {G}}{p _ {s} G _ {k} ^ {\mathrm{d}}}\right) ^ {t _ {2}}}{\alpha \Gamma (t _ {1} + 1) \Gamma (t _ {2} + 1)} \tag {27}
$$

$$
\times \left(\frac {r _ {\mathrm{min}} ^ {\mathrm{B}} \Gamma \left(\frac {\mathrm{B}}{\alpha} \mathrm{A} r _ {\mathrm{min}} ^ {\alpha}\right)}{\left(\mathrm{A} r _ {\mathrm{min}} ^ {\alpha}\right) ^ {\frac {\mathrm{B}}{\alpha}}} - \frac {r _ {\mathrm{max}} ^ {\mathrm{B}} \Gamma \left(\frac {\mathrm{B}}{\alpha} \mathrm{A} r _ {\mathrm{max}} ^ {\alpha}\right)}{\left(\mathrm{A} r _ {\mathrm{max}} ^ {\alpha}\right) ^ {\frac {\mathrm{B}}{\alpha}}}\right),
$$

where (a) is obtained using the approximated CDF of the SR fading in (12), (b) is from the relationship between the upper and lower incomplete gamma functions, i.e., $\begin{array} { r } { \frac { \gamma ( s , x ) } { \Gamma ( s ) } + \frac { \Gamma ( s , \dot { x } ) } { \Gamma ( s ) } = } \end{array}$ 1. In (c), since $\widetilde { \alpha _ { s } }$ is an integer, (c) is obtained from Γ $( n , { \dot { x } } ) =$

$$
(n - 1)! \mathrm{e} ^ {- x} \sum_ {k = 0} ^ {n - 1} \frac {x ^ {k}}{k !} [ 4 4 ].
$$

# D. Proof of Theorem 2

To obtain (17), we start with the definition of the end-to-end transmit rate capacity through the $k ^ { \mathrm { t h } }$ LEO satellite, which is shown in (28), at the top of the next page, where (a) is obtained by transforming the condition of both the uplink from the GU to the $k ^ { \mathrm { t h } }$ LEO satellite and the downlink from the $k ^ { \mathrm { t h } }$ LEO satellite to the GU to indicator functions; (b) employs the PDF of the SR fading model, which is given in (2); (c) is obtained by averaging $R _ { k }$ using the PDF in Lemma 1. □

# E. Proof of Theorem 3

In (18), there are three items, that is $T _ { k } ^ { \mathrm { u } } , \ T _ { k } ^ { \mathrm { d } }$ , and $( k - 1 ) T _ { \mathrm { h o } }$ . Due to their similar derivation steps, we take the first item as an example to start the derivation, given as

$$
\begin{array}{l} T _ {k} ^ {\mathrm{u}} \triangleq \frac {\omega}{B \log_ {2} \left(1 + \mathrm{SNR} _ {k} ^ {\mathrm{u}}\right)} \\ = \left(\frac {\omega}{B \log_ {2} \left(1 + \frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| H _ {k} ^ {\mathrm{u}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}}\right)} \right. \\ \end{array}
$$

$$
\begin{array}{l} \left. \right.\left| \right. \frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| H _ {k} ^ {\mathrm{u}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau , \frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| H _ {k} ^ {\mathrm{d}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\left. \right) \\ \stackrel {(a)} {=} \int_ {0} ^ {\infty} \int_ {0} ^ {\infty} \frac {\omega}{B \log_ {2} \left(1 + \frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| h _ {k} ^ {\mathrm{u}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}}\right)} \\ \times \mathbb {1} \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| h _ {k} ^ {\mathrm{u}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) \mathbb {1} \left(\frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| h _ {k} ^ {\mathrm{d}} \right| ^ {2} R _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) \\ \times f _ {\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{u}}\right) f _ {\left| H _ {k} ^ {\mathrm{d}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{d}}\right) d h _ {k} ^ {\mathrm{u}} d h _ {k} ^ {\mathrm{d}} \\ \end{array}
$$

$$
\stackrel {(b)} {=} \int_ {r _ {\min}} ^ {r _ {\max}} \int_ {0} ^ {\infty} \int_ {0} ^ {\infty} \frac {\omega}{B \log_ {2} \left(1 + \frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| h _ {k} ^ {\mathrm{u}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}}\right)}
$$

$$
\times \mathbb {1} \left(\frac {p _ {\mathrm{u}} G _ {k} ^ {\mathrm{u}} \left| h _ {k} ^ {\mathrm{u}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right) \mathbb {1} \left(\frac {p _ {\mathrm{s}} G _ {k} ^ {\mathrm{d}} \left| h _ {k} ^ {\mathrm{d}} \right| ^ {2} r _ {k} ^ {- \alpha}}{\mathcal {G}} > \tau\right)
$$

$$
\times f _ {\left| H _ {k} ^ {\mathrm{u}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{u}}\right) f _ {\left| H _ {k} ^ {\mathrm{d}} \right| ^ {2}} \left(h _ {k} ^ {\mathrm{d}}\right) f _ {R _ {k}} \left(r _ {k}\right) d h _ {k} ^ {\mathrm{u}} d h _ {k} ^ {\mathrm{d}} d r _ {k}, \tag {29}
$$

where (a) is obtained by applying the PDF of the SR fading model and converting the conditional probability into indicator functions; (b) is from the PDF of $R _ { k }$ in Lemma 1. Similarly, referring to the derivation above to average $T _ { k } ^ { \mathrm { d } }$ and $( k - 1 ) T _ { \mathrm { h o } }$ , we can obtain (20). □

# F. Proof of Proposition 2

To clearly characterize the dependence of the objective function on the number of serving satellites $K ,$ , we denote η by $F ( K )$ , expressed as $\begin{array} { r } { F ( K ) \triangleq \eta } \end{array}$ .

For any $K > 2 ,$ define the following quantities for notational simplicity

$$
a _ {k} \triangleq \bar {q} _ {k} P _ {k} (\tau), \quad b _ {k} \triangleq P _ {k} (\tau). \tag {30}
$$

Since $P _ { k } ( \tau )$ are $\bar { q } _ { k } P _ { k } ( \tau )$ are non-increasing with respect to $k , T _ { k }$ is non-decreasing with respect to k, we have

$$
\begin{array}{l} a _ {1} \geq a _ {2} \geq \dots \geq a _ {k}, \quad b _ {1} \geq b _ {2} \geq \dots \geq b _ {k}, \\ T _ {1} <   T _ {2} <   \dots <   T _ {k}. \end{array} \tag {31}
$$

$$
T _ {1} \leq T _ {2} \leq \dots \leq T _ {k}.
$$

Define

$$
U _ {K} \triangleq \prod_ {k = 1} ^ {K} \left(1 - a _ {k}\right), \quad V _ {K} \triangleq \prod_ {k = 1} ^ {K} \left(1 - b _ {k}\right), \tag {32}
$$

$$
Y _ {K} \triangleq (1 - U _ {K}) (1 - V _ {K}), \tag {33}
$$

$$
W _ {K} \triangleq T _ {1} + \sum_ {k = 2} ^ {K} T _ {k} V _ {k - 1}, \tag {34}
$$

Then, the objective function can be rewritten as

$$
F (K) = \frac {Y _ {K}}{W _ {K}}. \tag {35}
$$

Since K is a discrete variable, unimodality is established by studying the sign of the forward difference $F ( K + 1 ) - F ( K )$ .

From the definitions of $U _ { K }$ and $V _ { K }$ , we obtain

$$
U _ {K + 1} = U _ {K} \left(1 - a _ {K + 1}\right), \quad V _ {K + 1} = V _ {K} \left(1 - b _ {K + 1}\right). \tag {36}
$$

Hence,

$$
\begin{array}{l} \Delta Y _ {K} \triangleq Y _ {K + 1} - Y _ {K} \\ = (1 - U _ {K}) b _ {K + 1} V _ {K} + (1 - V _ {K}) a _ {K + 1} U _ {K} \\ + a _ {K + 1} b _ {K + 1} U _ {K} V _ {K}, \tag {37} \\ \end{array}
$$

and

$$
\Delta W _ {K} \triangleq W _ {K + 1} - W _ {K} = T _ {K + 1} V _ {K}. \tag {38}
$$

Therefore,

$$
\begin{array}{l} F (K + 1) - F (K) = \frac {Y _ {K} + \Delta Y _ {K}}{W _ {K} + \Delta W _ {K}} - \frac {Y _ {K}}{W _ {K}} \\ = \frac {W _ {K} \Delta Y _ {K} - Y _ {K} \Delta W _ {K}}{W _ {K} \left(W _ {K} + \Delta W _ {K}\right)}. \tag {39} \\ \end{array}
$$

Since the denominator is positive, the sign of $F ( K { + } 1 ) { - } F ( K )$ is determined by

$$
W _ {K} \Delta Y _ {K} - Y _ {K} \Delta W _ {K}. \tag {40}
$$

Define the marginal gain-to-cost ratio

$$
M _ {K} \triangleq \frac {\Delta Y _ {K}}{\Delta W _ {K}}. \tag {41}
$$

Then,

$$
F (K + 1) - F (K) = \frac {\Delta W _ {K}}{W _ {K} + \Delta W _ {K}} \left(M _ {K} - F (K)\right). \tag {42}
$$

Thus,

$$
F (K + 1) \geq F (K) \iff M _ {K} \geq F (K), \tag {43}
$$

and

$$
F (K + 1) \leq F (K) \iff M _ {K} \leq F (K). \tag {44}
$$

Therefore, the monotonic behavior of $F ( K )$ is fully characterized by the comparison between $M _ { K }$ and $F ( K )$ .

Using the expressions of $\Delta Y _ { K }$ and $\Delta W _ { K }$ , we have

$$
\begin{array}{l} M _ {K} = \frac {(1 - U _ {K}) b _ {K + 1}}{T _ {K + 1}} + \frac {(1 - V _ {K}) a _ {K + 1}}{T _ {K + 1}} \frac {U _ {K}}{V _ {K}} \\ + \frac {a _ {K + 1} b _ {K + 1} U _ {K}}{T _ {K + 1}}. \tag {45} \\ \end{array}
$$

Since $a _ { K + 1 }$ and $b _ { K + 1 }$ decrease with $K ,$ whereas $T _ { K + 1 }$ increases with K. From the physical interpretation, this means that when more serving satellites are included, the additional performance gain brought by the $\left( k + 1 \right) ^ { \mathrm { t h } }$ serving satellite becomes smaller, while the corresponding delay cost becomes larger. As a result, the marginal gain-to-cost ratio $M _ { K }$ is nonincreasing with respect to K, i.e.,

$$
M _ {K + 1} \leq M _ {K}. \tag {46}
$$

Suppose that for some $K ^ { ' }$ ,

$$
F \left(K ^ {\prime} + 1\right) \leq F \left(K ^ {\prime}\right). \tag {47}
$$

Then, from

$$
F (K + 1) - F (K) = \frac {\Delta W _ {K}}{W _ {K} + \Delta W _ {K}} \left(M _ {K} - F (K)\right), \tag {48}
$$

we obtain

$$
M _ {K ^ {\prime}} \leq F \left(K ^ {\prime}\right). \tag {49}
$$

On the other hand,

$$
\begin{array}{l} F \left(K ^ {\prime} + 1\right) = \frac {W _ {K ^ {\prime}}}{W _ {K ^ {\prime}} + \Delta W _ {K ^ {\prime}}} F \left(K ^ {\prime}\right) \tag {50} \\ + \frac {\Delta W _ {K ^ {\prime}}}{W _ {K ^ {\prime}} + \Delta W _ {K ^ {\prime}}} M _ {K ^ {\prime}}, \\ \end{array}
$$

which shows that $F ( K ^ { ' } + 1 )$ is a weighted average of $F ( K ^ { ' } )$ and $M _ { K ^ { \prime } }$ . Therefore,

$$
M _ {K ^ {\prime}} \leq F \left(K ^ {\prime} + 1\right) \leq F \left(K ^ {\prime}\right). \tag {51}
$$

Since $M _ { K }$ is non-increasing, we further have

$$
M _ {K ^ {\prime} + 1} \leq M _ {K ^ {\prime}} \leq F \left(K ^ {\prime} + 1\right). \tag {52}
$$

Hence,

$$
\begin{array}{l} F \left(K ^ {\prime} + 2\right) - F \left(K ^ {\prime} + 1\right) = \\ \frac {\Delta W _ {K ^ {\prime} + 1}}{W _ {K ^ {\prime} + 1} + \Delta W _ {K ^ {\prime} + 1}} \left(M _ {K ^ {\prime} + 1} - F \left(K ^ {\prime} + 1\right)\right) \leq 0. \tag {53} \\ \end{array}
$$

Repeating the same argument recursively yields

$$
F (K + 1) \leq F (K), \quad \forall K \geq K ^ {\prime}. \tag {54}
$$

Therefore, once $F ( K )$ starts to decrease, it will keep decreasing afterwards. This implies that the sequence $\{ F ( K ) \}$ can experience at most one transition from increasing to decreasing. Hence, $F ( K )$ is unimodal with respect to K when $K \geq 2 .$ .

Finally, although the case $K = 1$ is written separately for clarity, it is in fact the boundary case of the same objective function. Specifically, substituting $K \ : = \ : 1$ into the general expression yields $\begin{array} { r } { \dot { F } ( 1 ) ~ = ~ \frac { \bar { q } _ { k } P _ { 1 } ^ { \Xi } ( \tau ) } { T _ { 1 } } } \end{array}$ q¯k P 21 (τ ) , which is exactly the separately stated form. Therefore, the piecewise presentation introduces no inconsistency, and the unimodality result applies to the entire discrete domain $K \geq 1$ . □

This concludes the proof.

# REFERENCES

[1] Z. M. Bakhsh, Y. Omid, G. Chen, F. Kayhan, Y. Ma, and R. Tafazolli, “Multi-satellite MIMO systems for direct satellite-to-device communications: A survey,” IEEE Commun. Surv. Tutorials, vol. 27, no. 3, pp. 1536–1564, 2025.   
[2] H. Jia, C. Jiang, L. Kuang, and J. Lu, “An analytic approach for modeling uplink performance of mega constellations,” IEEE Trans. Veh. Technol., vol. 72, no. 2, pp. 2258–2268, 2023.   
[3] N. Pachler, E. F. Crawley, and B. G. Cameron, “Robust beam-to-satellite routing strategies for megaconstellations,” IEEE Wireless Commun. Lett., vol. 13, no. 11, pp. 3040–3043, 2024.   
[4] R. P. Perumal, H. Voos, F. D. Vedova, and H. Moser, “Small satellite reliability: A decade in review,” in AIAA/USU Conference on Small Satellites: Mission Operations & Autonomy, Logan, UT, USA, Aug. 2021.   
[5] X. Zhang, S. Sun, M. Tao, Q. Huang, and X. Tang, “Multi-satellite cooperative networks: Joint hybrid beamforming and user scheduling design,” IEEE Trans. Wireless Commun., vol. 23, no. 7, pp. 7938–7952, 2024.   
[6] X. Lu, M. Salehi, M. Haenggi, E. Hossain, and H. Jiang, “Stochastic geometry analysis of spatial-temporal performance in wireless networks: A tutorial,” IEEE Commun. Surv. Tutorials, vol. 23, no. 4, pp. 2753– 2801, 2021.   
[7] N. Okati, T. Riihonen, D. Korpi, I. Angervuori, and R. Wichman, “Downlink coverage and rate analysis of low Earth orbit satellite constellations using stochastic geometry,” IEEE Trans. Commun., vol. 68, no. 8, pp. 5120–5134, 2020.   
[8] N. Okati and T. Riihonen, “Nonhomogeneous stochastic geometry analysis of massive LEO communication constellations,” IEEE Trans. Commun., vol. 70, no. 3, pp. 1848–1860, 2022.   
[9] J. Park, J. Choi, and N. Lee, “A tractable approach to coverage analysis in downlink satellite networks,” IEEE Trans. Wireless Commun., vol. 22, no. 2, pp. 793–807, 2023.   
[10] A. Yastrebova, I. Angervuori, N. Okati, M. Vehkapera, M. H ¨ oyhty ¨ a,¨ R. Wichman, and T. Riihonen, “Theoretical and simulation-based analysis of terrestrial interference to LEO satellite uplinks,” in IEEE Global Communications Conference (GLOBECOM 2020), Dec. 2020.   
[11] A. Talgat, M. A. Kishk, and M.-S. Alouini, “Nearest neighbor and contact distance distribution for binomial point process on spherical surfaces,” IEEE Commun. Lett., vol. 24, no. 12, pp. 2659–2663, 2020.   
[12] ——, “Stochastic geometry-based analysis of LEO satellite communication systems,” IEEE Commun. Lett., vol. 25, no. 8, pp. 2458–2462, 2021.   
[13] D.-H. Jung, J.-G. Ryu, W.-J. Byun, and J. Choi, “Performance analysis of satellite communication system under the shadowed-Rician fading: A stochastic geometry approach,” IEEE Trans. Commun., vol. 70, no. 4, pp. 2707–2721, 2022.   
[14] Y. Sun and Z. Ding, “A fine grained stochastic geometry-based analysis on LEO satellite communication systems,” IEEE Netw. Lett., vol. 5, no. 4, pp. 237–240, 2023.   
[15] C.-S. Choi, “Modeling and analysis of downlink communications in a heterogeneous LEO satellite network,” IEEE Trans. Wireless Commun., vol. 23, no. 8, pp. 8588–8602, 2024.   
[16] H. Zhang, X. Miao, Z. Ni, S. Wang, G. Pan, C. Cavdar, and J. An, “LEO mega-constellation-terrestrial communications suffering Poisson arc hardcore distributed space interference,” IEEE Trans. Wireless Commun., vol. 24, no. 4, pp. 2707–2721, 2025.   
[17] B. Shang, X. Li, C. Li, and Z. Li, “Coverage in cooperative LEO satellite networks,” J. Commun. Inf. Netw., vol. 8, no. 4, pp. 329–340, 2023.   
[18] X. Li and B. Shang, “An analytical model for coordinated multi-satellite joint transmission system,” in Int. Conf. Ubiquitous Commun. (Ucom 2024), Xi’an, China, Oct. 2024.   
[19] M. Emara, A. Elzanaty, F. Benkhelifa, and R. Tafazolli, “A cooperative framework for enhanced direct-to-satellite connectivity,” in IEEE Int. Symp. Pers. Indoor Mob. Radio Commun. (PIMRC 2025), Istanbul, Turkiye, Dec. 2025.   
[20] X. Li and B. Shang, “Downlink performance of cell-free massive MIMO for LEO satellite mega-constellation,” IEEE Trans. Mob. Comput., vol. 25, no. 4, pp. 5117–5132, 2026.   
[21] M. Lee, S. Kim, M. Kim, D.-H. Jung, and J. Choi, “Analyzing downlink coverage in clustered low Earth orbit satellite constellations: A stochastic geometry approach,” IEEE Trans. Commun., vol. 73, no. 11, pp. 12 174– 12 188, 2025.   
[22] S. Yang, Y. Zhu, Y. Shi, W. Feng, and Q. Zhang, “Adaptive selecting in clustered LEO systems: Direct or cooperative communication?” IEEE Trans. Wireless Commun., vol. 25, pp. 12 050–12 065, 2026.

[23] R. Wang, M. A. Kishk, H. H. Yang, and M.-S. Alouini, “Analyzing localizability of LEO/MEO hybrid networks: A stochastic geometry approach,” IEEE Trans. Aerosp. Electron. Syst., vol. 61, no. 4, pp. 10 720–10 736, 2025.   
[24] J. Ru, R. Wang, and M.-S. Alouini, “Coverage and rate analysis of follower-based LEO satellite networks: A stochastic geometry approach,” IEEE Trans. Wireless Commun., vol. 25, pp. 12 662–12 675, 2026.   
[25] F. Qu, S. Lu, G. Xu, J. Shi, A. Nauman, and D. Niyato, “Coverage probability analysis and optimization for stochastic geometry-based multisatellite cooperative systems under dynamic channels,” IEEE Wireless Commun. Lett., vol. 15, pp. 91–95, 2026.   
[26] D. Kim, J. Park, and N. Lee, “Coverage analysis of dynamic coordinated beamforming for LEO satellite downlink networks,” IEEE Trans. Wireless Commun., vol. 23, no. 9, pp. 12 239–12 255, 2024.   
[27] X. Hu, B. Lin, X. Lu, P. Wang, N. Cheng, Z. Yin, and W. Zhuang, “Performance analysis of end-to-end LEO satellite-aided shore-to-ship communications: A stochastic geometry approach,” IEEE Trans. Wireless Commun., vol. 23, no. 9, pp. 11 753–11 769, 2024.   
[28] X. Lu, P. Wang, G. Li, D. Niyato, and Z. Li, “Short-packet backscatter assisted wireless-powered relaying with NOMA: Mode selection with performance estimation,” IEEE Trans. Cognit. Commun. Networking, vol. 8, no. 1, pp. 216–231, 2022.   
[29] Y. He, Z. Li, and Y. Chen, “Tractable modeling and performance analysis of low-Earth orbit satellite constellations,” IEEE Internet Things J., vol. 11, no. 17, pp. 28 297–28 306, 2024.   
[30] X. Lin, H. Zhang, G. Pan, S. Wang, and J. An, “LEO relay-aided GEO satellite-terrestrial transmissions,” IEEE Trans. Veh. Technol., vol. 72, no. 12, pp. 16 899–16 904, 2023.   
[31] R. Wang, M. A. Kishk, and M.-S. Alouini, “Ultra reliable low latency routing in LEO satellite constellations: A stochastic geometry approach,” IEEE J. Select. Areas Commun., vol. 42, no. 5, pp. 1231–1245, 2024.   
[32] N. Okati and T. Riihonen, “Stochastic analysis of satellite broadband by mega-constellations with inclined LEOs,” in IEEE Int. Symp. Pers. Indoor Mob. Radio Commun. (PIMRC 2020), London, UK, Aug. 2020.   
[33] J. Xu, M. A. Kishk, and M.-S. Alouini, “Space-air-ground-sea integrated networks: Modeling and coverage analysis,” IEEE Trans. Wireless Commun., vol. 22, no. 9, pp. 6298–6313, 2023.   
[34] K. A. Lee and J. R. Barry, “Outage analysis for all the satellites in a randomly distributed constellation,” in IEEE 21st Consumer Communications & Networking Conference (CCNC 2024), Las Vegas, NV, USA, Jan. 2024.   
[35] M. Can and I. Altunbas, “Outage probability analysis of rate-splitting multiple-access-based hybrid satellite–terrestrial relay network with relay selection,” IEEE Trans. Aerosp. Electron. Syst., vol. 59, no. 5, pp. 6508–6517, 2023.   
[36] A. Talgat, M. A. Kishk, and M.-S. Alouini, “Stochastic geometry-based uplink performance analysis of IoT over LEO satellite communication,” IEEE Trans. Aerosp. Electron. Syst., vol. 60, no. 4, pp. 4198–4213, 2024.   
[37] D.-H. Jung, J.-G. Ryu, and J. Choi, “When satellites work as eavesdroppers,” IEEE Trans. Inf. Forensics Secur., vol. 17, pp. 2784–2799, 2022.   
[38] X. Yuan, F. Tang, M. Zhao, and N. Kato, “Joint rate and coverage optimization for the THz/RF multi-band communications of space-airground integrated network in 6G,” IEEE Trans. Wireless Commun., vol. 23, no. 6, pp. 6669–6682, 2024.   
[39] A. K. Dwivedi, S. Chaudhari, N. Varshney, and P. K. Varshney, “Performance analysis of LEO satellite-based IoT networks in the presence of interference,” IEEE IoT J., vol. 11, no. 5, pp. 8783–8799, 2024.   
[40] H. Shi, N. Deng, B. Li, H. Wei, W. Lu, and N. Zhao, “Modeling and analysis of satellite-terrestrial covert communications,” Sci. China Inf. Sci., vol. 68, no. 9, p. 190306:1–190306:16, 2025.   
[41] R. Deng, B. Di, H. Zhang, L. Kuang, and L. Song, “Ultra-dense LEO satellite constellations: How many LEO satellites do we need?” IEEE Trans. Wireless Commun., vol. 20, no. 8, pp. 4843–4857, 2021.   
[42] B. Liu, L. Kuang, and J. Lu, “Performance analysis of NGSO satellite communication systems with flexible beams,” IEEE Internet Things J., vol. 11, no. 14, pp. 24 726–24 738, 2024.   
[43] Z. Jiang, W. Li, X. Wang, and B. Liang, “A LEO satellite handover strategy based on graph and multiobjective multiagent path finding,” Int. J. Aerosp. Eng., vol. 2023, no. 1, p. 1111557, 2023.   
[44] M. Alzenad and H. Yanikomeroglu, “Coverage and rate analysis for vertical heterogeneous networks (VHetNets),” IEEE Trans. Wireless Commun., vol. 18, no. 12, pp. 5643–5657, 2019.