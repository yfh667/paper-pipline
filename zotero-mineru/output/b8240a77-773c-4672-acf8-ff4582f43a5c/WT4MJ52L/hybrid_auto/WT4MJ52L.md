# Sustainability or Survivability? Eliminating the Need to Choose in LEO Satellite Constellations

Chris Misa

University of Oregon

# Abstract

LEO Satellite Networks (LSNs) are revolutionizing global connectivity, but their reliance on tens of thousands of satellites raises pressing concerns over sustainability and survivability. In this work, we argue that the inefficiencies in present-day LSN designs stem from ignoring the strong spatiotemporal structure of Internet traffic demand (which impacts sustainability) and the physical realities of the near-Earth space environment (which affects survivability). We propose a novel design approach based on sun-synchronous (SS) orbits called SS-plane, which aligns satellite coverage with the Earth’s diurnal cycle. We demonstrate that SS-plane constellations can reduce the number of satellites required by up to an order of magnitude and cut radiation exposure by ∼23% compared to traditional Walker-delta constellations. These findings suggest a paradigm shift in LSN research from large, disposable megaconstellations to more sustainable, targeted LEO constellations.

# CCS Concepts

• Networks → Network architectures; Network structure.

# Keywords

Satellite constellation design; satellite networking; space physics

# ACM Reference Format:

Chris Misa and Ramakrishnan Durairajan. 2025. Sustainability or Survivability? Eliminating the Need to Choose in LEO Satellite Constellations. In The 24th ACM Workshop on Hot Topics in Networks (HotNets ’25), November 17–18, 2025, College Park, MD, USA. ACM, New York, NY, USA, 8 pages. https://doi.org/10.1145/3772356. 3772408

# 1 Introduction

Low Earth Orbit (LEO) Satellite Networks (LSNs) are quickly becoming a cornerstone of global Internet infrastructure,

![](images/47a413eecd9a4dfac3559664c998ec2f1203b32da81660b5e0fc1b9f793104ba.jpg)

This work is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License.

HotNets ’25, College Park, MD, USA

© 2025 Copyright held by the owner/author(s).

ACM ISBN 979-8-4007-2280-6/25/11

https://doi.org/10.1145/3772356.3772408

Ramakrishnan Durairajan

University of Oregon and Link Oregon

offering fast, reliable connectivity nearly anywhere on the planet [3, 6, 15, 17, 19]. These systems are especially attractive for their potential to close the digital divide by delivering low-latency direct-to-consumer and transit service to regions of the planet that are difficult to connect with terrestrial network technologies [20, 22, 26, 35, 41, 42].

However, to meet both bandwidth demand and survivability goals, current LSNs require tens of thousands of satellites, raising serious concerns about their environmental impact and long-term sustainability [1, 2, 11, 27, 28, 31, 32, 40]. In particular, the limited capacity of a single satellite’s spotbeams implies LSNs must use overlapping coverage from many satellites to satisfy bandwidth demand of populated regions. Meanwhile, the harsh radiation environment of near-Earth space, coupled with cost pressures to reduce shielding, implies LSNs must operate extra in-orbit backup satellites to replace active satellites as they inevitably fail [10, 21]. Thus, there is a fundamental tension: reducing satellite count improves sustainability but jeopardizes survivability, while adding redundant satellites improves survivability but compromises sustainability.

Recent studies [9, 11, 16, 24] demonstrate dire environmental consequences of continuous launch and disposal in the upper atmosphere and inevitable instability resulting from overcrowding of limited physical LEO real estate if these pressures towards massive mega-constellations continue unabated. In response, the networking community has begun to explore design strategies that optimize satellite usage rather than maximize it [7, 21, 23]. A key observation of these strategies is that the spatial demand for satellite networking is sparse and clustered across the Earth surface whereas the supply of present-day LSNs is more-or-less uniform. LSNs could, in principle, be designed to provide nonuniform coverage to only the surface regions with higher demand, thereby reducing the number of satellites required.

Unfortunately, this purely spatial approach of designing more efficient LSNs is not feasible in practice. The relatively high velocity of satellites at LEO altitudes causes them to make ??(10) trips around the Earth each day, which (when combined with the natural rotation of the Earth w.r.t. satellite orbital planes) makes focusing LSN bandwidth supply in a spatially controlled and consistent manner nearly impossible. In particular, we show in § 2.2 that the recently proposed use of repeat ground-track (RGT) orbits [7, 23] performs strictly worse than present-day Walker-delta constellation designs in terms of the number of satellites required.

Instead of relying solely on spatial structure, our key insight is that LSN designs must also focus on temporal structure (i.e., the diurnal rhythms and seasonality of human Internet usage). Network traffic, especially in access ISP or mobile provider scenarios commonly targeted by LSNs, exhibits strong daily cycles caused by waking and sleeping hours [18, 25, 34]. Because the seasonality of each particular demand location on the Earth surface is synchronized with the Earth’s rotation on its axis, this implies traffic demand is actually fixed in space relative to the Sun.

This key insight opens up a tantalizing opportunity to rethink LSN constellation design. We argue that massive numbers of satellites are not an inherent requirement of satellite networking but rather a symptom of architectures that ignore the spatiotemporal structure of global demand and orbital hazards. To address this, we propose designing LSNs from a spatiotemporal perspective, treating both human activity patterns and orbital hazards as first-class design inputs.

To move beyond these abstract arguments, we introduce a new primitive for LSN design called sun-synchronous plane (henceforth SS-plane), based on sun-synchronous (SS) orbits [38]. SS-plane constellations align satellite coverage with the Sun-fixed rhythm of human demand, achieving more with fewer satellites. We show that SS-plane constellations can reduce satellite count by up to an order of magnitude compared to Walker-delta designs. They also expose satellites to significantly less radiation, lowering average exposure by up to 23%. Finally, we explore the implications of this approach for LSN research on topology design, routing, and traffic control.

What makes this work both timely and provocative is that we challenge the prevailing “more is better" philosophy behind today’s LEO megaconstellations. By showing that it is possible to dramatically reduce satellite count and radiation exposure through Sun-relative, demand-aware designs, we question the necessity of this design philosophy and its concomitant survivability and sustainability challenges. In doing so, we introduce a fundamentally different vision to rethink coverage not in geocentric but in heliocentric terms, aligning network infrastructure with human activity and refocusing LSN research on synchronizing supply and demand to the spinning Earth, not just to points fixed on its surface.

# 2 Background & Motivation

# 2.1 Why are present-day LSNs so big?

Present-day LSNs are immense in scale, often comprising thousands or even tens of thousands of satellites. For example, SpaceX recently announced plans to expand Starlink to nearly 30k satellites [8, 37]. This scale is primarily driven by two operational necessities: the need to meet growing bandwidth demands and the requirement for survivability in the face of frequent hardware failures.

In terms of bandwidth, on the one hand, a single satellite’s spot-beam capacity is limited (e.g., ??(10Mbps) for userfacing Ku-band [5, 30] and up to ∼100Gbps for backhaul Kaband [36, 39]). Hence, to support dense population centers with high data usage, overlapping coverage from multiple satellites is necessary [33]. This overlap inherently increases the number of satellites needed in orbit at any given time.

In terms of survivability, on the other hand, a chief hazard faced by LEO satellites is bombardment by various species of charged particles (e.g., electrons, protons) trapped in the Earth’s magnetic field which impact reliability and longevity of sensitive onboard networking equipment [13, 14, 32]. Since building highly shielded, fault-tolerant satellites would dramatically increase costs, current systems opt instead to keep spare satellites in orbit (e.g., 2-10 per orbital plane) [10, 21]. These spares can be quickly “hot-swapped” to replace failed units, but this redundancy further inflates the total satellite count. Thus, the prevailing approach in LSN design has treated satellites as cheap and disposable, reinforcing the trend toward massive constellations.

The LSN minimization challenge. This reality sets up the key design challenge for LSNs: how to minimize the number of satellites without compromising the system’s ability to meet bandwidth demand and maintain network survivability?

# 2.2 Repeat ground-track orbits are no silver bullet

Prior work [7, 23] attempted to address the LSN minimization challenge by using more efficient constellation geometries with non-uniform spatial coverage, turning to repeat groundtrack (RGT) orbits. These orbits have their altitudes (and hence orbital periods) carefully tuned against the spin of the Earth so that they retrace the same path over Earth’s surface on a regular basis, making them attractive for applications requiring consistent coverage of specific regions [38].

However, to ensure continuous coverage over time, a single repeat ground-track from LEO (e.g., using equally-spaced satellites with overlapping FOVs) requires more satellites than a minimal uniform coverage Walker-delta constellation at the same altitude as shown in Figure 1. For example, covering the RGT at 1215 km altitude requires ≥356 satellites compared to the ≥200 required for uniform global coverage in a Walker-delta constellation at the same altitude.

Moreover, at LEO altitudes the adjacent passes of the RGT are densely packed around the Earth’s circumference (as illustrated in Figure 2), leading to near-uniform global coverage anyway. Figure 1 confirms that only three of the possible

![](images/95146366f59218f94d1ce2c665328c816be4fd7285a4c843116c07decc836bd2.jpg)

<details>
<summary>line</summary>

| Altitude (km) | RGT (unif.) | RGT (non-unif.) | Walker (total) |
| ------------- | ----------- | --------------- | -------------- |
| 500           | 3           | 1000            | 1000           |
| 1000          | 2           | 5               | 5              |
| 1500          | 1           | 3               | 3              |
| 2000          | 1           | 1               | 1              |
</details>

Figure 1: Minimum number of satellites required to cover a single repeat ground-track compared to number of satellites required for uniform global coverage in a Walker-delta constellation at 65° inclination.

RGTs considered do not automatically provide uniform global coverage.1

Key takeaway. The limitations of both traditional Walkerdelta and RGT orbits expose a critical shortcoming in existing constellation strategies: a lack of alignment with the actual structure of user demand. Any effort to reduce the number of satellites meaningfully must account for where and when bandwidth is needed—not just how to cover the Earth uniformly. This insight motivates a shift toward demand-centric design principles that better reflect the spatiotemporal nature of global Internet usage.

More broadly, the inefficiencies of current LSNs stem not just from their geometric designs but from a more fundamental mismatch between satellite coverage (largely uniform) and human activity (strongly non-uniform).

# 3 Structural Considerations in the LSN Design Problem

To move toward more sustainable and survivable constellations, design approaches must first leverage the intrinsic structure of Internet bandwidth demand (§ 3.1) and second the natural structure of near-Earth radiation (§ 3.2).

# 3.1 The structure of bandwidth demand

The primary driver behind designing efficient LSNs lies in understanding the structure of Internet bandwidth demand. Bandwidth usage is highly non-uniform across both space and time. Although specific patterns will likely vary across different anticipated LSN usecases (e.g., connecting rural ISPs vs. providing in-flight connectivity), we posit that spatial and temporal structures similar to the following will likely persist in some form across a wide range of usecases.

![](images/101fa1865932afd37c741c60f17e0dbe63f47afa3b0231a67006d6aa39854ab3.jpg)

<details>
<summary>natural_image</summary>

World map with a red circle highlighting a specific region, overlaid with a wavy black grid pattern (no text or labels)
</details>

Figure 2: Example of a repeat ground-track with inclination 65°, altitude ∼560 km and the surface region coverage by a single satellite covering this ground-track (in red).

Spatial structure. Network bandwidth demand mirrors the highly non-uniform spatial distribution of human population across the Earth surface. Intermediate latitudes which are home to much of the world’s population experience particularly high demand, while polar and oceanic regions see minimal usage. This skewed distribution suggests that uniform satellite coverage is an inefficient strategy, as it dedicates significant resources to areas with little or no demand.

To illustrate we consider the SEDAC Gridded World Population Density [12] data which estimates the population density of a 0.5°-wide grid over the Earth surface. Figure 3 shows the maximum population density over all longitudes for each latitude indicating significant clustering of population at intermediate latitudes.

Temporal structure. Temporally, Internet traffic driven by human activity exhibits pronounced daily cycles. Usage rises during waking hours and drops sharply at night. This diurnal pattern repeats reliably and is aligned with the Earth’s rotation, meaning that peak usage in any given region is tied to local solar time.

To illustrate, we consider the CESNET-TimeSeries24 dataset which includes fine-granularity throughput measurements from 283 sites across the Czech Republic over 40 weeks [18]. To summarize the daily seasonality in this dataset, we normalize throughput at each site by the site’s median (to account for relative differences between sites) and group by time of day. Figure 4 shows the resulting relationship between time of day and normalized bandwidth demand (median and 95-percentile over all sites).

Spatiotemporal structure. Intuitively, we can combine the data from Figure 3 and Figure 4 by scaling the bandwidth demand at each point in time by the population density at each point in space to approximate the spatiotemporal structure of bandwidth demand.

To illustrate, Figure 5 shows the time-adjusted bandwidth demand at four distinct points in time throughout the day for the entire Northern Hemisphere. At each point in time we rotate the Earth such that the Sun is in the direction of the top of the page. Though it is somewhat obfuscated by the large absolute differences in population density at different longitudes, clear “quieter” and “louder“ regions are apparent. (For example, the right-hand side of each figure corresponds to the early hours of the morning and remains dark whereas the top corresponds to midday and remains light.)

![](images/f3c441bcff9c9d9bba06a9b7b9ab6b3dac941b00a88e834fff357dcc645f1c96.jpg)

<details>
<summary>line</summary>

| Latitude (deg) | Pop. #/km^2 |
| -------------- | ----------- |
| -90            | 0           |
| -60            | 0           |
| -30            | 2000        |
| 0              | 6000        |
| 30             | 7000        |
| 60             | 6000        |
| 90             | 0           |
</details>

Figure 3: Maximum global population density at each latitude aggregated in 0.5° bins (from [12]).

![](images/d4919f8db75e074d81395fb2b2e8b74b2a695c7a713549f4f233333da4fa0b84.jpg)

<details>
<summary>line</summary>

| Time of day (H) | 50-th | 95-th |
| --------------- | ----- | ----- |
| 0               | 50    | 1000  |
| 2               | 40    | 800   |
| 4               | 50    | 1000  |
| 6               | 100   | 2000  |
| 8               | 150   | 1500  |
| 10              | 150   | 1500  |
| 12              | 150   | 1500  |
| 14              | 100   | 1000  |
| 16              | 80    | 800   |
| 18              | 60    | 600   |
| 20              | 50    | 500   |
| 22              | 40    | 400   |
</details>

Figure 4: Normalized bandwidth demand as a function of local time-of-day across 283 sites in CESNET [18].

![](images/45f9841f93e6c0c72658b26a833625f5d217764978e5ee676d73afa343ca26ab.jpg)

<details>
<summary>natural_image</summary>

Satellite view of Earth showing continents and oceans with visible cloud patterns (no text or labels)
</details>

(a) Hour 0

![](images/ac4f55ccab1980c126430300e7f21b105cf072af44e9356a996f59aa8913fd5a.jpg)

<details>
<summary>natural_image</summary>

Satellite view of Earth showing continents and oceans (no text or labels visible)
</details>

(b) Hour 6

![](images/16c143a0879278bf0aa7a58c8ed81ad1f43c63e6c59d1ae52f81b5b606f04e70.jpg)

<details>
<summary>natural_image</summary>

Satellite view of Earth showing continents and oceans with visible cloud patterns (no text or labels)
</details>

(c) Hour 12

![](images/3577f7fba601217228edfda1642ad21a401addd0401a0d651440b0e9cee78dc1.jpg)

<details>
<summary>natural_image</summary>

Satellite view of Earth showing continents and oceans with visible cloud patterns (no text or labels)
</details>

(d) Hour 18   
Figure 5: Spatio-temporal model of global Internet demand (viewed from directly above the North Pole with the Sun at the top of the page).

Key takeaway. A spatiotemporal view of bandwidth demand reveals that Internet usage is neither globally uniform nor temporally static. Rather, demand follows predictable patterns tied to both geography and local time, suggesting that satellite constellations should be engineered not around Earth’s surface, but around the Sun-relative structure of human activity.

# 3.2 Near-Earth radiation

A secondary driver behind increased numbers of satellites is the need to maintain spare satellites to be swapped in when active satellites fail.

Though satellite failures may originate from a variety of causes, we posit a persistent cause of failure to be exposure to radiation (i.e., energetic electrons, protons, and other ions) trapped in the Earth’s magnetic field [14]. Although satellites can be built with shielding to protect sensitive electronic components from this radiation, doing so increases both the cost of each satellite and the total mass of material. Hence reducing aggregate radiation exposure of a satellite constellation reduces the number of spare satellites required for replacing failures as well as the costs of each individual satellite.

To understand the structure of near-Earth radiation fields, we leverage IRENE, a state-of-the-art dataset and model designed specifically for pre-mission estimates of radiation exposure in Earth orbit [4]. To illustrate, Figure 6 shows IRENE’s estimate of radiation flux for satellites at 560 km altitude. Because radiation intensity and structure strongly depend on solar activity, we aggregate over a sample of 128 days randomly selected from solar cycle 24.

![](images/7b7be34e20377dd5cfbe7eadcc2cf34913c3eb56b38d5684eb17e5ffd0571faf.jpg)

<details>
<summary>natural_image</summary>

World map with color-coded temperature gradient from purple to yellow, showing ocean currents and latitude/longitude lines (no text labels)
</details>

Figure 6: Maximum electron flux at 560 km altitude over a sample of 128 days from solar cycle 24.

Several key spatial structures are apparent in Figure 6. First, a large region of high radiation intensity sits over South America and the South Atlantic—commonly referred to as the South Atlantic Anomaly [13]. Second, distinct bands of high radiation intensity cross over moderate-to-high Southern and Northern latitudes. These structures result from the intersection of the orbital altitude with the “inner” and “outer” Van Allen “belts” respectively [29].

The key implication of the structure—particularly of the outer Van Allen belt—for LSN design is that the commonlyused moderate inclination orbits $( e . g . , 6 0 ^ { \circ }$ to 70°) actually represent a worst-case scenario from a radiation perspective. Intuitively, this is because orbital trajectories at this inclination “turn around” at their Southern- and Northern-most points directly in these radiation bands, increasing their overall radiation exposure. In contrast, lower inclination orbits turn around before reaching the radiation band and higher inclination orbits quickly pass through the band to turn around at higher latitudes. To illustrate this effect, Figure 7 shows the average radiation accumulation over a full day for orbits at the same altitude as a function of inclination.

![](images/285f533d22c113a0ed021246f5b26761f58110572c99b6c50156b2a805a41361.jpg)

<details>
<summary>bar</summary>

| Inclination (deg) | Fluence (#/cm^2/MeV) |
| ----------------- | --------------------- |
| 50                | 4                     |
| 60                | 6                     |
| 70                | 7                     |
| 80                | 6                     |
| 90                | 6                     |
</details>

(a) Electrons

![](images/b37f8de74e544b5deeed4431ef2e7a268a8d8f85632c2050b1cbc2fa3986e759.jpg)

<details>
<summary>bar</summary>

| Inclination (deg) | Fluence (#/cm^2/MeV) |
| ----------------- | --------------------- |
| 60                | 15M                   |
| 60                | 35M                   |
| 60                | 30M                   |
| 60                | 25M                   |
| 60                | 20M                   |
| 60                | 15M                   |
| 60                | 10M                   |
| 80                | 10M                   |
| 80                | 25M                   |
| 80                | 30M                   |
| 80                | 35M                   |
| 80                | 30M                   |
| 80                | 25M                   |
| 80                | 20M                   |
| 80                | 15M                   |
| 80                | 10M                   |
</details>

(b) Protons   
Figure 7: Estimated daily radiation exposure for 560 km orbits as a function of inclination.

Key takeaway. Radiation exposure is not uniform across LEO, and inclination plays a decisive role in determining cumulative satellite damage. By selecting orbits that avoid high-radiation regions we can enhance satellite durability and reduce redundancy requirements, thereby lowering both operational risk and environmental cost.

# 4 Towards High-efficiency LSN Designs

The above insights into the spatiotemporal nature of bandwidth demand and the structured distribution of radiation exposure warrant a rethinking of LSN design. Instead of aiming for geometric uniformity, we believe future constellation designs should exploit the regularity and predictability inherent in both user behavior and radiation distribution. In this section, we introduce one such design called SS-plane.

# 4.1 A sun-synchronous (SS) perspective on demand

Building on the discussion of § 3.1, we propose a “sun-synchronous” (SS) perspective on bandwidth demand and LSN constellation design. The key defining feature of SS orbits is that they pass over any particular latitude at a single, fixed local time of day (e.g., always ascending over the equator at noon). This is achieved by tuning inclination and altitude so that the natural precession of the orbital plane corresponds exactly to the motion of the Earth around the Sun. SS orbits require inclinations greater than 90° making them “retrograde” orbits whose ground-tracks move from East to West (rather than from West to East as is the case for most present-day LSNs). Though such orbits have slightly higher launch costs (because extra fuel is required to counter the momentum inherited from the rotation of the Earth), we anticipate their long-term savings for constellation design will out-weigh these one-time launch costs. For example, the Earth’s rotation at the equator is about 6% of the orbital velocity of the altitude considered in § 4.3 and can be reduced be leveraging launch sites at higher latitude.

To understand the utility of SS orbits for LSN design, consider a non-rotating latitude vs. “local time of day” grid fixed w.r.t. the direction of the Sun (instead of the usual latitude vs. longitude grid fixed to the Earth’s rotating surface). Each particular latitude, time-of-day point on this grid sees all longitudes as the Earth rotates and hence must be able to provide up to the maximum bandwidth demanded at that latitude scaled for the point’s particular (fixed) time of day. To illustrate, Figure 8 shows such a latitude, time-of-day grid estimated from the data discussed in § 3.1. The clustering of demand along latitude corresponds to the clustering of population density shown in Figure 3 and the structure of demand along time-of-day corresponds to the temporal structure shown in Figure 4.

![](images/bc128d80e41f6f32a84b62f8969f94b5095982ba99fea5e3a9c54d030b3ffaac.jpg)

<details>
<summary>heatmap</summary>

| Lat. (deg) | 0    | 6    | 12   | 18   | 24   |
|------------|------|------|------|------|------|
| 90         | 0    | 50   | 50   | 50   | 50   |
| 45         | 0    | 50   | 50   | 50   | 50   |
| 0          | 0    | 50   | 50   | 50   | 50   |
| -45        | 0    | 50   | 50   | 50   | 50   |
| -90        | 0    | 50   | 50   | 50   | 50   |
</details>

Figure 8: Visualization of spatiotemporal structure of demand as a function of the local time-of-day.

Intuitively, an LSN whose orbital trajectories are fixed to this latitude, time-of-day grid while satisfying the demand at each grid point is also able to satisfy the demand of the (rotating) latitude, longitude grid on the Earth’s surface.

# 4.2 Covering the demand map

Our key method is to generate “planes” of SS orbits which correspond to fixed paths on the latitude vs. time-of-day bandwidth demand grid. The SS-plane constellation design problem is then a matter of selecting a set of such planes so that the demand at each grid point is satisfied and the number of satellites is minimized.

To efficiently compute approximate solutions to this optimization problem, we develop the following greedy algorithm.

(1) Select a latitude, time-of-day point that has the maximum bandwidth demand.   
(2) Add an SS-plane that intersects that point and subtract the capacity of one satellite from all latitude, time-ofday points covered by the plane’s path (clamping to zero).   
(3) If all demand is satisfied, return the accumulated set of planes, otherwise go back to (1).

Because each added SS-plane covers a relatively large range of latitude, time-of-day points (in addition to the maximumdemand point), this algorithm quickly generates sets of planes that cover all spatiotemporal demand even though it may not find the exact minimum.

# 4.3 Initial performance evaluation

We evaluate our approach by considering the spatiotemporal bandwidth demand shown in Figure 8. To avoid dependence on the bandwidth capacity of a particular satellite design or radio technology, we measure bandwidth demand in multiples of the capacity of a single satellite (i.e., “bandwidth multiplier”). We consider a single orbital altitude (∼560 km) and compare against Walker-delta (WD) constellations constructed of multiple shells (e.g., slightly above and below this altitude) at different inclinations determined by maximum population density at each latitude.

Figure 9 shows the number of satellites required to meet bandwidth demand for both constellation design methods. At lower bandwidth demands, our approach is able to leverage spatiotemporal demand non-uniformity whereas the Walker-delta constellation requires more satellites to maintain uniform coverage. As demand increases, our approach’s SS-planes begin saturating the latitude vs. time-of-day grid, leading to a reduction in the difference between methods.

Figure 10 compares the same constellations in terms of their median per-satellite radiation exposure (accumulated over one day using IRENE). Because all SS-planes have the same inclination, the median radiation exposure does not

![](images/f4b4a212d90a6d631522f5f0bc809eacec989e6343afe2056364cbda59f457d7.jpg)

<details>
<summary>line</summary>

| Bandwidth multiplier | SS    | WD    |
| -------------------- | ----- | ----- |
| 10                   | 1000  | 10000 |
| 2                    | 1000  | 10000 |
| 5                    | 1000  | 10000 |
| 100                  | 2000  | 10000 |
| 2                    | 5000  | 10000 |
| 5                    | 10000 | 10000 |
| 1000                 | 20000 | 20000 |
| 2                    | 50000 | 50000 |
| 5                    | 100000| 100000|
</details>

Figure 9: Number of satellites required to satisfy the spatiotemporal structure shown in Figure 8 as a function of the total bandwidth demand (measured in multiples of a single satellite’s bandwidth capacity).

change as more planes are added. However, for the Walkerdelta constellations, the use of lower inclinations to target higher population densities leads to higher median radiation exposure across the constellation (see Figure 3 and Figure 6).

![](images/b4a47f18b734136693baf4a897bb9778e732f37dfcfe944b6a4f83b4aca21b52.jpg)

<details>
<summary>line</summary>

| Bandwidth multiplier | SS     | WD     |
| -------------------- | ------ | ------ |
| 10                   | 7B     | 7.5B   |
| 100                  | 7B     | 7.5B   |
| 1000                 | 7B     | 8B     |
</details>

(a) Electrons

![](images/c9c5138029f0ac1cd038c545065f05619b51f4a16ecebfabe854984209e07323.jpg)

<details>
<summary>line</summary>

| Bandwidth multiplier | SS     | WD     |
| -------------------- | ------ | ------ |
| 10                   | 10M    | 11M    |
| 100                  | 10M    | 11M    |
| 1000                 | 10M    | 13M    |
</details>

(b) Protons   
Figure 10: Estimated median radiation exposure over one day for a satellite in the constellations evaluated in Figure 9.

Key Takeaway. Together, these results demonstrate that sun-synchronous constellations not only require significantly fewer satellites to meet realistic spatiotemporal demand, but also reduce exposure to harmful radiation. Furthermore, these benefits represent a compelling path forward for designing LEO networks that are not only more efficient and survivable, but also more environmentally and economically sustainable.

# 5 Implications for Networking

Traditional networking strategies for LSNs have assumed uniform, always-available infrastructure. However, SS-plane constellations bring spatiotemporal awareness to the forefront. LSN research must now account for predictable, dynamic coverage patterns that follow the Earth’s relation to the Sun rather than its rotational geography. This fundamental shift opens up a robust LSN research agenda:

(1) How can we design time-aware satellite network topologies and routing protocols that proactively exploit predictable spatiotemporal variations in sun-synchronous constellations? First, network topology design must adapt to a constellation layout that is inherently non-uniform in time and space. Routing protocols must be capable of handling predictable gaps and surges in connectivity, possibly by precomputing timeaware paths and schedules. Moreover, bandwidth allocation and scheduling algorithms should exploit the regularity of human activity to prioritize peak-hour service and shift nonurgent traffic to off-peak periods. In other words, network layers must figure out how to leverage the physical capacity enabled by SS-plane constellations while ensuring target service levels are met during on-peak as well as off-peak periods.

(2) What fault-tolerance and traffic management strategies are best suited to low-failure, high-efficiency LEO constellations? The reduced failure rate due to lower radiation exposure also alters the survivability paradigm. With fewer random outages, networks can adopt lighter-weight failure recovery mechanisms. This opens the door for more efficient use of bandwidth and lower latency in fault detection and re-routing. Additionally, the smaller number of satellites simplifies inter-satellite link management, reducing the complexity of coordination and congestion avoidance.

(3) What simulation methodologies and traffic models are required to accurately evaluate LEO network performance in SS-plane constellations? These changes also highlight the need for new simulation tools and modeling frameworks. Future research must incorporate Sun-relative spatiotemporal traffic models into the design, simulation, and verification of satellite network protocols.

(4) How should the control plane architecture of satellite networks evolve to incorporate solar-relative demand modeling, predictive resource allocation, and integration with terrestrial networks for seamless end-to-end service delivery? At a broader architectural level, SS constellations represent a shift toward spatiotemporally optimized infrastructure. Future network control planes may need to incorporate solar-relative models of demand and availability as first-class primitives. This shift suggests that satellite network controllers, whether centralized or distributed, should evolve to operate on Sun-relative coordinates, periodically updated with bandwidth forecasts, satellite health, and user load predictions. Integration with terrestrial Internet systems will also need to be revisited, particularly in terms of dynamic handoff between satellites and ground stations, latency-sensitive peering, and caching.

# Acknowledgments

We thank our shepherd Shaddi Hasan and anonymous reviewers for their constructive feedback. This work is supported by the National Science Foundation (CNS-2145813) and Internet Society (ISOC) Foundation. The views and conclusions contained herein are those of the authors and should not be interpreted as necessarily representing the official policies or endorsements, either expressed or implied, of NSF or ISOC.

# References

[1] [n. d.]. Mega-Constellations Pose Massive Risks to Shared Space Access. https://www.fierce-network.com/sponsored/megaconstellations-pose-massive-risks-to-shared-space-access. Accessed 2025-05-29.   
[2] [n. d.]. Satellite Licensing: FCC Should Reexamine Its Environmental Review Process for Large Constellations of Satellites. https://www. gao.gov/products/gao-23-105005. Accessed 2025-05-29.   
[3] [n. d.]. US agency approves T-Mobile, SpaceX license to extend covereage to dead zones. https://www.reuters.com/technology/usagency-approves-t-mobile-spacex-license-extend-coverage-deadzones-2024-11-26/. Accessed: 2025-05.   
[4] Air Force Research Laboratory (AFRL). [n. d.]. IRENE-AE9/AP9/SPM Home. https://www.vdl.afrl.af.mil/programs/ae9ap9/. Accessed: 2025- 07.   
[5] Simon Alvarez. 2024. Starlink shares demo of first-ever Direct to Cell satellite video call. https://www.teslarati.com/starlink-direct-to-cellvideo-call-demo-video/. Accessed: 2025-10.   
[6] Debopam Bhattacherjee and Ankit Singla. 2019. Network topology design at 27,000 km/hour. In Proceedings of the 15th International Conference on Emerging Networking Experiments And Technologies. 341–354.   
[7] Yimei Chen, Lixin Liu, Yuanjie Li, Hewu Li, Qian Wu, Jun Liu, and Zeqi Lai. 2024. Unraveling Physical Space Limits for LEO Network Scalability. In Proceedings of the 23rd ACM Workshop on Hot Topics in Networks. 43–51.   
[8] CSI. [n. d.]. SpaceX to launch massive Starlink V3 satellites with low latency. https://www.csimagazine.com/csi/SpaceX-to-launch-massive-StarlinkV3-satellites-with-low-latency.php. Accessed: 2025-07.   
[9] Andrea D’Ambrosio, Simone Servadio, Peng Mun Siew, Daniel Jang, Miles Lifson, and Richard Linares. 2022. Analysis of the LEO orbital capacity via probabilistic evolutionary model. In 2022 AAS/AIAA Astrodynamics Specialist Conference, Charlotte, North Carolina, August 7, Vol. 11.   
[10] FCC. [n. d.]. Satellite communications services (FCC Report No. SES-02767). https://docs.fcc.gov/public/attachments/DOC-411304A1.pdf. Accessed: 2025-07.   
[11] José P Ferreira, Ziyu Huang, Ken-ichi Nomura, and Joseph Wang. 2024. Potential ozone depletion from satellite demise during atmospheric reentry in the era of mega-constellations. Geophysical Research Letters 51, 11 (2024), e2024GL109280.   
[12] Center for International Earth Science Information Network (CIESIN). [n. d.]. SEDAC: Gridded World Population. https://earth.gov/ ghgcenter/data-catalog/sedac-popdensity-yeargrid5yr-v4.11. Accessed: 2025-07.   
[13] Kirolosse M Girgis, Tohru Hada, Shuichi Matsukiyo, and Akimasa Yoshikawa. 2022. Radiation analysis of LEO mission in the South Atlantic anomaly during geomagnetic storm. IEEE Journal of Radio Frequency Identification 6 (2022), 292–298.   
[14] Timothy B Guild, Scott C Davis, Alex J Boyd, T Paul O’Brien, Joseph F Fennell, Joseph E Mazur, Douglas G Brinkman, Glenn E Peterson, and Alan B Jenkin. 2022. Best Practices for Generating Space Environment Specification with Modern Tools. Aerospace Corporation.   
[15] Mark Handley. 2018. Delay is not an option: Low latency routing in space. In Proceedings of the 17th ACM Workshop on Hot Topics in Networks. 85–91.   
[16] Daniel Jang, Andrea D’Ambrosio, Miles Lifson, Celina Pasiecznik, and Richard Linares. 2022. Stability of the LEO Environment as a Dynamical System. In Advanced Maui Optical and Space Surveillance Technologies (AMOS) Conference.

[17] Simon Kassing, Debopam Bhattacherjee, André Baptista Águas, Jens Eirik Saethre, and Ankit Singla. 2020. Exploring the" Internet from space" with Hypatia. In Proceedings of the ACM Internet Measurement conference. 214–229.   
[18] Josef Koumar, Karel Hynek, Tomáš Čejka, and Pavel Šiška. 2025. CESNET-TimeSeries24: Time Series Dataset for Network Traffic Anomaly Detection and Forecasting. Scientific Data 12, 1 (2025), 338.   
[19] Zeqi Lai, Hewu Li, Yangtao Deng, Qian Wu, Jun Liu, Yuanjie Li, Jihao Li, Lixin Liu, Weisen Liu, and Jianping Wu. 2023. StarryNet: Empowering researchers to evaluate futuristic integrated space and terrestrial networks. In 20th USENIX Symposium on Networked Systems Design and Implementation (NSDI 23). 1309–1324.   
[20] Zeqi Lai, Weisen Liu, Qian Wu, Hewu Li, Jingxi Xu, Yibo Wang, Yuanjie Li, and Jun Liu. 2024. SpaceRTC: Unleashing the Low-latency Potential of Mega-constellations for Wide-Area Real-Time Communications. IEEE Transactions on Mobile Computing (2024).   
[21] Zeqi Lai, Yibo Wang, Hewu Li, Qian Wu, Qi Zhang, Yunan Hou, Jun Liu, and Yuanjie Li. 2024. Your Mega-Constellations Can Be Slim: A Cost-Effective Approach for Constructing Survivable and Performant LEO Satellite Networks. In IEEE INFOCOM 2024-IEEE Conference on Computer Communications. IEEE, 521–530.   
[22] Jihao Li, Hewu Li, Zeqi Lai, Qian Wu, Yijie Liu, Qi Zhang, Yuanjie Li, and Jun Liu. 2024. Satguard: Concealing endless and bursty packet losses in leo satellite networks for delay-sensitive web applications. In Proceedings of the ACM Web Conference 2024. 3053–3063.   
[23] Yuanjie Li, Yimei Chen, Jiabo Yang, Jinyao Zhang, Bowen Sun, Lixin Liu, Hewu Li, Jianping Wu, Zeqi Lai, Qian Wu, et al. 2025. Small-scale LEO Satellite Networking for Global-scale Demands. In Proceedings of the ACM SIGCOMM 2025 Conference. 917–931.   
[24] J-C Liou and Nicholas L Johnson. 2008. Instability of the present LEO satellite populations. Advances in Space Research 41, 7 (2008), 1046–1053.   
[25] Gabriel Maciá-Fernández, José Camacho, Roberto Magán-Carrión, Pedro García-Teodoro, and Roberto Therón. 2018. UGR ‘16: A new dataset for the evaluation of cyclostationarity-based network IDSs. Computers & Security 73 (2018), 411–424.   
[26] Doug Madory. [n. d.]. Starlink Enters Transit Market With Community Gateways. https://www.kentik.com/blog/starlink-enters-transitmarket-with-community-gateways/. Accessed: 2025-07.   
[27] Christopher Maloney, Robert Portmann, Karen H Rosenlof, and Charles Bardeen. 2024. Stratospheric loading and radiative impacts from increased Al2O3 emission caused by an anticipated increase in satellite re-entry frequency. In AIAA SCITECH 2024 Forum. 2169.   
[28] Christopher M Maloney, Robert W Portmann, Martin N Ross, and Karen H Rosenlof. 2025. Investigating the potential atmospheric accumulation and radiative impact of the coming increase in satellite reentry frequency. Journal of Geophysical Research: Atmospheres 130,

6 (2025), e2024JD042442.   
[29] BH Mauk, NJ Fox, SG Kanekal, RL Kessel, DG Sibeck, and A Ukhorskiy. 2013. Science Objectives and Rationale for the Radiation Belt Storm Probes Mission. Space Science Reviews 179, 1-4 (2013), 3–27.   
[30] Christopher Mclain and James Hetrick. 2014. High throughput kuband for aero applications. In 30th AIAA International Communications Satellite System Conference (ICSSC). 15085.   
[31] Amy Mehlman, John P. Janka, and Mark A. Sturza. [n. d.]. Averting Environmental Risks In The New Space Age. https://fas.org/publication/ averting-environmental-risks-in-the-new-space-age/. Accessed 2025- 05-29.   
[32] Chris Misa and Ramakrishnan Durairajan. 2025. The Internet from Space, Reimagined: Leveraging Altitude for Efficient Global Coverage. In Proceedings of the 3rd Workshop on LEO Networking and Communication. 57–63.   
[33] Mike Puchol. [n. d.]. Modeling Starlink capacity. https://mikepuchol. com/modeling-starlink-capacity-843b2387f501. Accessed: 2025-07.   
[34] Zhiming Shen, Qin Jia, Gur-Eyal Sela, Ben Rainero, Weijia Song, Robbert van Renesse, and Hakim Weatherspoon. 2016. Follow the sun through the clouds: Application migration for geographically shifting workloads. In Proceedings of the Seventh ACM Symposium on Cloud Computing. 141–154.   
[35] Aleksandr Stevens, Blaise Iradukunda, Brad Bailey, and Ramakrishnan Durairajan. 2024. Can LEO Satellites Enhance the Resilience of Internet to Multi-hazard Risks?. In International Conference on Passive and Active Network Measurement. Springer, 170–195.   
[36] DEV Systemtechnik. [n. d.]. Ka-Band Diversity Case Study. https: //dev-systemtechnik.com/kaband-diversity/. Accessed: 2025-10.   
[37] Advanced Television. [n. d.]. SpaceX files with FCC for V3. https://www.advanced-television.com/2024/10/18/spacex-fileswith-fcc-for-v3/. Accessed: 2025-07.   
[38] David A Vallado. 2001. Fundamentals of astrodynamics and applications. Vol. 12. Springer Science & Business Media.   
[39] Michael Waldow. 2023. Maximizing Ka-Band Network Updatime by Ground Station Diversity. https://interactive.satellitetoday.com/via/ articles/maximizing-ka-band-network-uptime-by-ground-stationdiversity. Accessed: 2025-10.   
[40] Constance Walker, Jeffrey Hall, Lori Allen, Richard Green, Patrick Seitzer, Tony Tyson, Amanda Bauer, Kelsie Krafton, James Lowenthal, Joel Parriott, et al. 2020. Impact of satellite constellations on optical astronomy and recommendations toward mitigations. Bulletin of the American Astronomical Society 52, 2 (2020).   
[41] Jinwei Zhao and Jianping Pan. 2024. Low-Latency Live Video Streaming over a Low-Earth-Orbit Satellite Network with DASH. In Proceedings of the 15th ACM Multimedia Systems Conference. 109–120.   
[42] Kelsey Ziser. [n. d.]. Telesat is no Starlink. https://www.lightreading. com/satellite/telesat-is-no-starlink. Accessed: 2025-07.