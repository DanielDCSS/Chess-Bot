#include <VarSpeedServo.h>

//Decalring the servos:
VarSpeedServo servo1; //Rotation
VarSpeedServo servo2; //Arm
VarSpeedServo servo3; //Forearm
VarSpeedServo servo4; //Claw

//Declaring the speed:
int speed = 15;


//Declaring the pin:
int pin1 = 2;

//Declaring the button:
int RobotTurnButton;


//Declaring the coordinate arrays:
int Rotation[66] = {
    64, 71, 79, 87, 96, 105, 114, 121,
    67, 73, 81, 88, 95, 103, 111, 117,
    68, 75, 82, 87, 95, 102, 110, 115,
    71, 76, 84, 92, 98, 103, 110, 115,
    74, 78, 84, 89, 95, 100, 106, 113,
    75, 79, 85, 89, 94, 99, 106, 111,
    75, 79, 84, 89, 94, 97, 104, 107,
    73, 79, 83, 88, 93, 97, 102, 105,
    180, 0
};
int Arm_Down[66] = {
    52, 46, 49, 48, 44, 47, 48, 48,
    60, 57, 56, 55, 55, 56, 57, 57,
    65, 64, 63, 61, 61, 61, 63, 63,
    74, 69, 69, 66, 66, 68, 71, 71,
    80, 74, 76, 76, 76, 76, 76, 77,
    87, 88, 83, 83, 83, 83, 87, 88,
    102, 96, 94, 94, 94, 94, 98, 99,
    117, 116, 111, 108, 108, 108, 111, 117,
    61, 60
};
int Forearm_Down[66] = {
    60, 61, 56, 56, 56, 56, 60, 61,
    58, 57, 53, 52, 52, 53, 56, 58,
    68, 60, 62, 65, 65, 65, 62, 65,
    70, 70, 71, 67, 67, 67, 66, 70,
    76, 78, 76, 76, 76, 76, 76, 79,
    87, 87, 84, 84, 84, 84, 85, 87,
    97, 93, 92, 92, 92, 92, 96, 96,
    117, 114, 107, 104, 104, 104, 109, 117,
    65, 60
};
int Arm_Up[66] = {
    24, 18, 21, 20, 16, 19, 20, 20,
    35, 32, 31, 30, 30, 31, 32, 32,
    43, 42, 41, 39, 39, 39, 41, 41,
    54, 49, 49, 46, 46, 48, 51, 51,
    63, 57, 59, 59, 59, 59, 59, 60,
    72, 73, 68, 68, 68, 68, 72, 73,
    90, 84, 82, 82, 82, 82, 86, 87,
    100, 99, 94, 91, 91, 91, 94, 100,
    39, 60
};
int Forearm_Up[66] = {
    121, 122, 117, 117, 117, 117, 121, 122,
    107, 106, 102, 101, 101, 102, 105, 107,
    106, 98, 100, 103, 103, 103, 100, 103,
    105, 105, 106, 102, 102, 102, 101, 105,
    108, 110, 108, 108, 108, 108, 108, 111,
    116, 116, 113, 113, 113, 113, 114, 116,
    126, 122, 121, 121, 121, 121, 125, 125,
    147, 144, 137, 134, 134, 134, 139, 147,
    103, 60
};

//Declaring the claw positions:
  int Claw_Open = 90;
  int Claw_Closed = 130;


//Declaring the move array:
int Movement[5]; //{origin square, destination square, capture (boolean), capture square, castle (0 or 1 or 2)}




void Move(int Origin, int Destination)
{
servo1.slowmove (Rotation[Origin], speed);
servo2.slowmove (Arm_Up[Origin], speed);
servo3.slowmove (Forearm_Up[Origin], speed);

servo4.slowmove (Claw_Open, speed);

delay(500);

servo2.slowmove (Arm_Down[Origin], speed);
servo3.slowmove (Forearm_Down[Origin], speed);

delay(500);

servo4.slowmove (Claw_Closed, speed);

delay(500);

servo2.slowmove (Arm_Up[Origin], speed);
servo3.slowmove (Forearm_Up[Origin], speed);

delay(500);

servo1.slowmove (Rotation[Destination], speed);
servo2.slowmove (Arm_Up[Destination], speed);
servo3.slowmove (Forearm_Up[Destination], speed);

delay(500);

servo2.slowmove (Arm_Down[Destination], speed);
servo3.slowmove (Forearm_Down[Destination], speed);

delay(500);

servo4.slowmove (Claw_Open, speed);

delay(500);

servo2.slowmove (Arm_Up[Destination], speed);
servo3.slowmove (Forearm_Up[Destination], speed);

delay(500);

}




void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  
  pinMode(pin1, INPUT_PULLUP);

   
  //Attaching the servos to pins:
  servo1.attach(6);
  servo2.attach(9);
  servo3.attach(10);
  servo4.attach(11);
}

void loop() {
  // put your main code here, to run repeatedly:
  
  //Assigning the button to pin:
  RobotTurnButton = digitalRead(pin1);
  
 
  //Instructions for if the robot needs to move ball from position 1 to 2:
  if(RobotTurnButton == LOW) {
    if (Movement[4] == 1){
      Move(0, 64);
      Move(4, 2);
      Move(64, 3);

    }
    else if (Movement[4] == 2){
      Move(7, 64);
      Move(4, 6);
      Move(64, 5);

    }
    else if (Movement[2] == true){
      Move(Movement[3], 65);
      Move(Movement[0], Movement[1]);

    }
    else {
      Move(Movement[0], Movement[1]);

    }
  }
}