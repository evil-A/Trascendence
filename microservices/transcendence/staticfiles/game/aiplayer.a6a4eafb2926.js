import Player from "./local_player.js";

class AIPlayer extends Player
{
    //The AI oponent is allways on the left.
    constructor(canvas)
    {
        super(true, canvas, false);
        this.canvas_width = canvas.width
        this.last_position_calculated = -1;
        this.last_ball_position = [this.canvas_width/2, this.canvas_height/2];
        this.predicted_ball_height = this.canvas_height/2;
    }

    calculate_next_collision(ball_position, ball_speed)
    {
        let t = Math.abs(ball_position[0]/ball_speed[0]);
        if (ball_speed[0] > 0)
        {
            t = 2*this.canvas_width/ball_speed[0] - t;
        }
        let h = ball_position[1] + t*ball_speed[1];
        this.previous_position = ball_position;
        while(h > this.canvas_height || h < 0)
        {
            if (h < 0)
            {
                h *= -1;
            }
            if (h > this.canvas_height)
            {
                h = this.canvas_height - (h - this.canvas_height)
            }
        }
        this.predicted_ball_height = h + (Math.random()*2 - 1)*this.height*0.6;
    }
    
    calculate_move(ball_position, ball_speed)
    {
        let time = Date.now();
        if (this.last_position_calculated < 0 || (time - this.last_position_calculated) > 1000)
        {
            this.calculate_next_collision(ball_position, ball_speed);
            this.last_position_calculated = time;
        }
        if(this.y + this.height/2 < this.predicted_ball_height)
        {
            this.move(1);
        }
        if(this.y + this.height/2 > this.predicted_ball_height)
        {
            this.move(-1);
        }
    }
}

export default AIPlayer;