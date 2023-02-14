Wakurtosis Load Simualtor (WSL)
===============================

Kurtosis: https://docs.kurtosis.com/

### How to use:

To build docker image:
    `sh ./build.sh`

Name of the image is wsl:0.0.1

### Parameters

- _simulation_time_: int. Default: **300**. Specifies the simulation time in seconds.
- _message_rate_: int. Default: **25**. Specifies the message rate in packets per second.
- _min_packet_size_: int. Default: **1**. Specifies the minimum size of the packet in bytes. Must be an even number (Waku constrain).
- _min_packet_size_: int. Default: **1024**. Specifies the maximum size of the packet in bytes. Must be an even number (Waku constrain).
- _dist_type_: int. Default: **uniform**. Specifies the size distribution of the messages being injected into the network. Options are: **gaussian** and **uniform**
- _emitters_fraction_: int. Default: **0.5**. Specifies the fraction of nodes that will be injecting traffic.
- _inter_msg_type_: int. Default: **poisson**. Specifies the inter-message times. Options are: **poisson** and **uniform**

dist_type : "gaussian"

    # Fraction (of the total number of nodes) that inject traffic
    # Values: [0., 1.]
    emitters_fraction : 0.5

    # Inter-message times
    # Values: uniform and gaussian
    inter_msg_type : "uniform"