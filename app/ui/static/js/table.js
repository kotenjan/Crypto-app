function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// rendering and data of gui prediction table
new Vue({
    el: '#table',
    data(){
        return{
            crypto:[],
            new_crypto:"",
            new_symbol:"",
        }
    },
    methods:{
        // periodically request new data
        async refreshData(){
            while (true){
                try {
                    const response = await fetch('http://127.0.0.1:5000/data/');
                    const data = await response.json();
                    if (data.success){
                        this.crypto = data.data;
                        console.log('UPDATED')
                    }
                    else{
                        alert(data.message)
                    }    
                } catch (error) {
                    alert('Failed to get table data')
                }
                await sleep(5 * 1000);
            }
        },

        addClick(){
            this.new_crypto="";
            this.new_symbol="";
        },

        async createClick(){
            try {
                const response = await fetch('http://127.0.0.1:5000/add/?name=' + this.new_crypto + '&symbol=' + this.new_symbol);
                const data = await response.json();
                if (data.success){
                    this.crypto = data.data;
                }
                else{
                    alert(data.message)
                }    
            } catch (error) {
                console.log('Failed to add new crypto')
            }
        },

        async deleteClick(id){
            try {
                if (confirm('The cryptocurrency ' + id + ' will be deleted')){
                    const response = await fetch('http://127.0.0.1:5000/remove/?name=' + id);
                    const data = await response.json();
                    if (data.success){
                        this.crypto = data.data;
                    }
                    else{
                        alert(data.message)
                    }    
                }
            } catch (error) {
                console.log('Failed to remove crypto')
            }
        },    
    },
    mounted:function(){
        this.refreshData();
    },
    // change of delimiters in html code
    delimiters: ['[[',']]']
})