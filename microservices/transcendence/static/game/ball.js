class Ball{
    constructor(canvas)
    {
        this.size = canvas.width*.02;
        this.resetBall(canvas);
    }

    resetBall(canvas)
    {
        this.x = canvas.width/2;
        this.y = canvas.height/2;
        this.speedX = Math.random() > .5 ? canvas.width*.005 : -canvas.width*.005;
        this.speedY = this.speedX * (Math.random() - .5)*2;
    }
    
    draw(context)
    {
        context.beginPath();
        context.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        context.fill();
    }

    move(canvas)
    {
        this.x += this.speedX;
        this.y += this.speedY;

        if (this.y < this.size || this.y > canvas.height - this.size){
            this.speedY *= -1;
        }
    }
}

export default Ball