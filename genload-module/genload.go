package main

import (
	  //"context"
	"flag"
	"fmt"
	  //"net"
	  //"bytes"
  //"math/rand"
    //"strconv"
	  //"encoding/binary"
	  //"os"
	 "time"

	logging "github.com/ipfs/go-log/v2"
	  //"github.com/multiformats/go-multiaddr"
	  //"github.com/waku-org/go-waku/waku/v2/dnsdisc"
	  //"github.com/waku-org/go-waku/waku/v2/node"
	  //"github.com/waku-org/go-waku/waku/v2/payload"
	  //"github.com/waku-org/go-waku/waku/v2/protocol/pb"
	  //"github.com/waku-org/go-waku/waku/v2/utils"

	//"crypto/rand"
	//"encoding/hex"
	//"github.com/ethereum/go-ethereum/crypto"
	//"github.com/waku-org/go-waku/waku/v2/protocol/filter"
	//"github.com/waku-org/go-waku/waku/v2/protocol"

  //"github.com/wadoku/wadoku/utils"
)

var log = logging.Logger("GenLoad: ")
const StartPort = 60000
const PortRange = 1000

var nodeType = "lightpush"
var seqNumber int32 = 0


type config struct {
	log_level                 string
	output_fname              string
  min_msg_size              int            //  min packet size
  max_msg_size              int            // max packet size
	msg_size_distribution     string         // Inter-arrival distribution
  msg_rate                  int            // per-node message rate
	msg_arrival_distribution  string         // Inter-arrival distribution
	emitters_fraction         float64        // Emitter's fraction
	simulation_time           time.Duration  // Duration of the simulation
}

var conf = config{}
func ArgInit(){
	flag.StringVar(&conf.log_level, "l", "info",
		"Specify the log level")
	flag.StringVar(&conf.output_fname, "o", "output.out",
		"Specify the output file")
	flag.IntVar(&conf.min_msg_size, "m", 1024,
		"Specify the minimal packet size")
	flag.IntVar(&conf.max_msg_size, "x", 10240,
		"Specify the maximal packet size")
	flag.StringVar(&conf.msg_size_distribution, "s", "tnormal",
		"Specify the message size distribution")
	flag.IntVar(&conf.msg_rate, "r", 10,
		"Specify the per-node message rate")
	flag.StringVar(&conf.msg_arrival_distribution, "a", "poisson",
		"Specify the message arrival distribution")
	flag.Float64Var(&conf.emitters_fraction, "e", 10,
		"Specify the fraction of nodes to generate the load")
	flag.DurationVar(&conf.simulation_time, "d", 60*time.Second,
		"Specify the duration (1s,2m,4h)")
}

func init() {
	// args
  fmt.Println("Populating CLI params...")
  ArgInit()
}


func main() {

	flag.Parse()

	// setup the log  
	lvl, err := logging.LevelFromString(conf.log_level)
	if err != nil {
		panic(err)
	}
	logging.SetAllLoggers(lvl)
  fmt.Println(conf)
}
