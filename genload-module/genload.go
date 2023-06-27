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
  min_msg_size              int            // Min packet size
  max_msg_size              int            // Max packet size
	msg_size_distribution     string         // Message size distribution
  msg_rate                  int            // Per-node message rate
	msg_arrival_distribution  string         // Inter-arrival distribution
	emitters_fraction         float64        // Emitter's fraction
	simulation_time           time.Duration  // Duration of the simulation
  config_file               string         // Config file name
}

var conf = config{}
func ArgInit(){
	flag.StringVar(&conf.log_level, "log-level", "info",
		"Specify the log level")
	flag.StringVar(&conf.output_fname, "output-dir", "output.out",
		"Specify the output file")
	flag.IntVar(&conf.min_msg_size, "min-msg-size", 1024,
		"Specify the minimal packet size")
	flag.IntVar(&conf.max_msg_size, "max-msg-size", 10240,
		"Specify the maximal packet size")
	flag.StringVar(&conf.msg_size_distribution, "msg-size-distribution", "tnormal",
		"Specify the message size distribution")
	flag.IntVar(&conf.msg_rate, "message-rate", 10,
		"Specify the per-node message rate")
	flag.StringVar(&conf.msg_arrival_distribution, "msg-arrival-distribution", "poisson",
		"Specify the message arrival distribution")
	flag.Float64Var(&conf.emitters_fraction, "emitters-fraction", 10,
		"Specify the fraction of nodes to generate the load")
	flag.DurationVar(&conf.simulation_time, "simulation-time", 60*time.Second,
		"Specify the duration (1s,2m,4h)")
	flag.StringVar(&conf.config_file, "config-file", "config.json",
		"Specify the config.json")
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
/*
  // Let's first read the `config.json` file
    content, err := ioutil.ReadFile("./config.json")
    if err != nil {
        log.Fatal("Error when opening file: ", err)
    }

    // Now let's unmarshall the data into `payload`
    var payload Data
    err = json.Unmarshal(content, &payload)
    if err != nil {
        log.Fatal("Error during Unmarshal(): ", err)
    }
*/
  fmt.Println(conf)
}
