package main

import (
	"context"
	"flag"
	"fmt"
	"net"
	  //"bytes"
  "math/rand"
  "strconv"
	  //"encoding/binary"
	  //"os"
	 "time"
   "encoding/json"
   "io/ioutil"

	logging "github.com/ipfs/go-log/v2"
	  //"github.com/multiformats/go-multiaddr"
	  //"github.com/waku-org/go-waku/waku/v2/dnsdisc"
	  "github.com/waku-org/go-waku/waku/v2/node"
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
const localHost =  "0.0.0.0"
const startPort = 60000
const portRange = 1000

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

func uniform_distribution(min_size, max_size int) {
  // generate uniform distri
}

func rtnormal_distribution(min_size, max_size int) {
  mean, sd := (max_size - min_size) / 2, (max_size - min_size) / 5
  fmt.Println(mean, sd)
  // generate uniform distri
}

func main() {

	flag.Parse()

	// setup the log  
	lvl, err := logging.LevelFromString(conf.log_level)
	if err != nil {
		panic(err)
	}
	logging.SetAllLoggers(lvl)

  // Read the `config.json` as a json_dump
  json_dump, err := ioutil.ReadFile(conf.config_file)
  if err != nil {
       log.Fatal("Error when opening file: ", err)
   }

   // Unmarshall json dump
   var jsonmap map[string]interface{}
   err = json.Unmarshal(json_dump, &jsonmap)
   if err != nil {
        log.Fatal("Error during Unmarshal(): ", err)
   }

   // TODO: now config.json takes precedence. make cli take precedence
  var payload map[string]interface{} = jsonmap["genload"].(map[string]interface{})
  conf.min_msg_size             = int(payload["min_msg_size"].(float64))
  conf.max_msg_size             = int(payload["max_msg_size"].(float64))
	conf.msg_size_distribution    = payload["msg_size_distribution"].(string)
  conf.msg_rate                 = int(payload["msg_rate"].(float64))
	conf.msg_arrival_distribution = payload["msg_arrival_distribution"].(string)
	conf.emitters_fraction        = payload["emitters_fraction"].(float64)
	conf.simulation_time          = time.Duration(payload["simulation_time"].(float64))

  tcpEndPoint :=  localHost +
                      ":" +
                      strconv.Itoa(startPort +  rand.Intn(portRange))
	// create the waku node  
	hostAddr, _ := net.ResolveTCPAddr("tcp", tcpEndPoint)
	ctx := context.Background()
  lightpushNode, err := node.New(
		node.WithHostAddress(hostAddr),
		//node.WithNTP(),  // don't use NTP, fails at msec granularity
		//node.WithWakuRelay(),
		//node.WithLightPush(), // no need to add lightpush to be a lightpush client! 
	)
  fmt.Println(ctx, lightpushNode)
	if err != nil {
		panic(err)
	}

  fmt.Println(conf)
}
