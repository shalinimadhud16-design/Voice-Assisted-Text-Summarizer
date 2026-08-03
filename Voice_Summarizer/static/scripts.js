document.getElementById('audioForm').addEventListener('submit', function(event) { 
    event.preventDefault(); // Prevent the default form submission

  const submitButton = event.submitter || document.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;
    const chart_div = document.getElementById('chartContainer');
            chart_div.style.display='none';

    // Disable button and show loading state
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Loading';

    const formData = new FormData(this);
    const results = document.getElementById('results');
    results.style.display = 'none';

    fetch('/process_audio', {
        method: 'POST',
        body: formData // Send the FormData as the request body
    })
    .then(response => response.json())
    .then(data => {
      chart_div.style.display='block';
        results.style.display = 'block'; // Show results
        document.getElementById('transcript').textContent = data.transcript;
        
        // Display sentiment exactly as received from the server
        document.getElementById('sentiment').textContent = data.sentiments;
        document.getElementById('summary').textContent = data.summary;
        // Display overall sentiment
                updateDoughnutChart(data.sentiments);
        document.getElementById('overall_sentiment').textContent = data.overall_sentiment;
    })
    .catch(error => {
        console.error('Error:', error);
    }).finally(() => {
        // Reset button to original state
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;

    });
});

 let sentimentChart;

        // Function to initialize the doughnut chart with zero values
        function initializeDoughnutChart() {
            const ctx = document.getElementById('sentimentChart').getContext('2d');
            
            sentimentChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['joy', 'anger', 'sadness', 'fear', 'neutral', 'surprise', 'disgust'],
                    datasets: [{
                        data: [0, 0, 0, 0, 0, 0, 0], // Initial values are zeros
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF'
                        ],
                        hoverBackgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        // Function to update the doughnut chart with new data
        function updateDoughnutChart(responseString) {
            const sentimentData = JSON.parse(responseString.replace(/'/g, '"')); // Convert to JSON
            const dataValues = [
                sentimentData.joy || 0,
                sentimentData.anger || 0,
                sentimentData.sadness || 0,
                sentimentData.fear || 0,
                sentimentData.neutral || 0,
                sentimentData.surprise || 0,
                sentimentData.disgust || 0
            ];
            const chart_div = document.getElementById('chartContainer');
            chart_div.style.display='block';
            console.log(dataValues);
            sentimentChart.data.datasets[0].data = dataValues; // Update data
            sentimentChart.update(); // Refresh the chart
        }

        // Initialize the chart
        initializeDoughnutChart();