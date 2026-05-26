from flask import Flask, render_template, request
from scanner_logic import scan_ports, analyze_headers, calculate_grade, audit_ssl
from datetime import datetime 

app = Flask(__name__)

# Add this simple filter so the HTML can count open ports
@app.template_filter('filter_open_count')
def filter_open_count(ports):
    return len([p for p in ports if p['state'] == 'open'])


@app.route('/', methods=['GET', 'POST'])
def home():
    
    results = None
    target = None
    
    if request.method == 'POST':
        target = request.form.get('target')
        
        # 1. Run the scans to create the data
        port_data, p_score = scan_ports(target)
        header_data, h_score = analyze_headers(target)
        ssl_msg, ssl_score = audit_ssl(target)
        ssl_status = "SECURE" if ssl_score == 0 else "CRITICAL"
        
        # 2. Calculate final grade
        final_score = p_score + h_score + ssl_score
        grade = calculate_grade(final_score)
        
        # 3. NOW create the results dictionary
       
        results = {
            'ports': port_data,
            'headers': header_data,
            'score': final_score,
            'grade': grade,
            'ssl_msg': ssl_msg,
            'ssl_status': ssl_status,
            'p_score': p_score,
            'h_score': h_score,
            'ssl_score': ssl_score,
            'time': datetime.now().strftime("%H:%M:%S") # Just add this line
        }
    return render_template('index.html', results=results, target=target)

if __name__ == '__main__':
    app.run(debug=True)