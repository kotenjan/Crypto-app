// vue.js makes calls to get data from server
// there is sleep interval after every call in loop
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// the chart settings
Vue.component('line-chart', {
    extends: VueChartJs.Line,
    mixins: [VueChartJs.mixins.reactiveProp],
    props: ['chartData'],
    data: function() {
        return {
            options: {
                responsive: true, 
                maintainAspectRatio: false,
                legend: {
                    // makes sure visible data stay visible and hidden stay hidden after data update from server
                    onClick(e, legendItem) {
                        const index = legendItem.datasetIndex;
                        const ci = this.chart;
                        var meta = ci.getDatasetMeta(index);
                        meta.hidden = meta.hidden === null? !ci.data.datasets[index].hidden : null;
                        this.chart.data.datasets[index].hidden = !this.chart.data.datasets[index].hidden
                        ci.update();
                    },
                },
                animation: {
                    duration: 0
                },
                tooltips: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    xAxes: [{
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: 'Time'
                        }
                    }],
                    // each dataset has it's own axes because of the value differences
                    // improves visibility and comparability
                    yAxes: [{
                        display: true,
                        "id": "y1",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                        ticks: {
                            display: false
                        },
                    },{
                        display: false,
                        "id": "y2",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y3",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y4",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y5",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y6",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y7",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y8",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y9",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y10",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y11",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y12",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y13",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y14",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y15",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y16",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y17",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y18",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y19",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y20",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y21",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y22",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y23",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y24",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y25",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y26",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y27",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y28",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y29",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    },{
                        display: false,
                        "id": "y30",
                        scaleLabel: {
                            display: true,
                            labelString: 'Value'
                        },
                    }],
                }
            }
        }
    },
    // data is being updated only on demand
    // server sends flag signaling when to render new data
    created() {
        this.$watch('chartData.data.update_flag', (newQuestion) => {
            this.$data._chart.update();
        })
    },
    // Initialize and render the chart
    mounted() {
        this.renderChart(this.chartData.data, this.options); 
    },
})

var vm = new Vue({
    el: '#chart',
    data() {
        return {
            chartData: {
                'data': {
                    'update_flag': -1, // flag for update
                    'labels': [], // chart labels
                    'datasets': [] // datasets
                }
            },
            // Text on the button under chart
            isActive: false,
            // makes the visibility of each dataset persist even after changing chart view
            visibility: {}, 
        }
    },
    methods: {
        // replace data and update their visibility
        process(data){
            if (this.chartData.data.update_flag != data.update_flag){
                this.chartData.data.labels = data.labels;

                // set the visibility of datasets based on previously saved info 
                this.chartData.data.datasets.forEach((dataSetChart, j) => {
                    this.visibility[dataSetChart.label] = this.chartData.data.datasets[j].hidden
                })
                data.datasets.forEach((dataSetRes, i) => {
                    this.chartData.data.datasets.forEach((dataSetChart, j) => {
                        if (dataSetRes.label in this.visibility){
                            data.datasets[i].hidden = this.visibility[dataSetRes.label]
                        }
                        else if (dataSetRes.label == dataSetChart.label){
                            data.datasets[i].hidden = this.chartData.data.datasets[j].hidden
                        }
                    })
                })
                
                this.chartData.data.datasets = data.datasets;
                this.chartData.data.update_flag = data.update_flag;
            }    
        },
        // change chart view between overview and predictions
        async toggle() {
            this.isActive = !this.isActive;
            try {
                const response = await fetch('http://127.0.0.1:5000/mode/?limit=' + 1440);
                const data = await response.json();
                this.process(data)    
            } catch (error) {
                console.log('Failed to load chart')
            }
        },
        // periodically request chart data
        async fillData() {
            while (true) {
                try {
                    const response = await fetch('http://127.0.0.1:5000/chart/?limit=' + 1440);
                    const data = await response.json();
                    this.process(data)    
                } catch (error) {
                    console.log('Failed to load chart')
                }
                await sleep(20 * 1000);    
            }
        }
    },
    created() {
        this.fillData();
    },
    delimiters: ['[[',']]']
})