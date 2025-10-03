from flask import Flask, render_template


app = Flask(__name__)

root = ''
@app.route(f"/{root}")
def list_users():
    return render_template(f"{root}.html")

if __name__ == "__main__":
    app.run(debug=True)
    
    
    
    
    