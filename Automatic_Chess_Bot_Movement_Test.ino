#include <VarSpeedServo.h>

//Decalring the servos:
VarSpeedServo servo1; //Rotation
VarSpeedServo servo2; //Arm
VarSpeedServo servo3; //Forearm
VarSpeedServo servo4; //Claw

//Declaring the speed:
int speed = 15;
int Delay = 1000;
float M = 0.5;
//Declaring the pin:
int pin1 = 2;
int pinT = 4;

//Declaring the button:
int RobotTurnButton;


//Declaring the coordinate arrays:
int Rotation[66] = {
    64, 70, 78, 87, 96, 105, 113, 122,
    65, 71, 79, 87, 95, 103, 111, 119,
    67, 74, 80, 87, 95, 102, 109, 116,
    71, 76, 84, 92, 98, 103, 110, 115,
    74, 78, 84, 89, 95, 103, 106, 113,
    75, 79, 85, 89, 94, 99, 106, 111,
    75, 79, 84, 89, 94, 97, 104, 107,
    73, 79, 83, 88, 93, 97, 102, 105,
    180, 0
};
int Arm_Down[66] = {
    52, 50, 47, 45, 44, 47, 48, 50,
    60, 58, 57, 55, 55, 55, 55, 57,
    65, 62, 60, 61, 61, 61, 62, 63,
    74, 69, 69, 66, 66, 68, 71, 71,
    80, 74, 76, 76, 76, 76, 76, 77,
    87, 88, 83, 83, 83, 83, 87, 88,
    102, 96, 94, 94, 94, 94, 98, 99,
    117, 116, 111, 108, 108, 108, 111, 117,
    61, 60
};
int Forearm_Down[66] = {
    58, 55, 57, 56, 56, 55, 59, 59,
    60, 59, 57, 55, 56, 58, 60, 64,
    68, 67, 66, 65, 65, 65, 69, 69,
    70, 70, 71, 67, 67, 67, 66, 70,
    76, 78, 76, 76, 76, 76, 76, 79,
    87, 87, 84, 84, 84, 84, 85, 87,
    97, 93, 92, 92, 92, 92, 96, 96,
    117, 114, 107, 104, 104, 104, 109, 117,
    65, 60
};
int Arm_Up[66] = {
    24, 18, 18, 20, 16, 19, 20, 20,
    35, 32, 31, 30, 30, 31, 32, 32,
    43, 42, 41, 39, 39, 39, 41, 40,
    54, 49, 49, 46, 46, 48, 51, 51,
    63, 57, 59, 59, 59, 59, 59, 60,
    72, 73, 68, 68, 68, 68, 72, 73,
    90, 84, 82, 82, 82, 82, 86, 87,
    100, 99, 94, 91, 91, 91, 94, 100,
    39, 60
};
int Forearm_Up[66] = {
    121, 122, 117, 117, 117, 117, 121, 122,
    107, 106, 102, 101, 101, 102, 105, 110,
    106, 98, 100, 103, 103, 103, 105, 120,
    105, 105, 106, 102, 102, 102, 101, 105,
    108, 110, 108, 108, 108, 108, 108, 111,
    116, 116, 113, 113, 113, 113, 114, 116,
    126, 122, 121, 121, 121, 121, 125, 125,
    147, 144, 137, 134, 134, 134, 139, 147,
    103, 60
};

//Declaring the claw positions:
  int Claw_Open = 85;
  int Claw_Closed = 128;


//Declaring the move array:
int Movement[5]; //{origin square, destination square, capture (boolean), capture square, castle (0 or 1 or 2)}




void Move(int Origin, int Destination)
{
digitalWrite(pinT, HIGH);

delay(50);

servo1.slowmove (Rotation[Origin], speed);
servo2.slowmove (Arm_Up[Origin], speed);
servo3.slowmove (Forearm_Up[Origin], speed);

servo4.slowmove (Claw_Open, speed);

delay(2*Delay);

servo2.slowmove (Arm_Down[Origin], M*abs(Arm_Down[Origin]-Arm_Up[Origin]));
servo3.slowmove (Forearm_Down[Origin], M*abs(Forearm_Up[Origin]-Forearm_Down[Origin]));

delay(Delay);

servo4.slowmove (Claw_Closed, speed);

delay(Delay+500);

servo2.slowmove (Arm_Up[Origin], speed);
servo3.slowmove (Forearm_Up[Origin], speed+5);

delay(Delay);

servo1.slowmove (Rotation[Destination], speed);
servo2.slowmove (Arm_Up[Destination], speed);
servo3.slowmove (Forearm_Up[Destination], speed);

delay(2*Delay);

servo2.slowmove (Arm_Down[Destination], M*abs(Arm_Down[Destination]-Arm_Up[Destination]));
servo3.slowmove (Forearm_Down[Destination], M*abs(Forearm_Up[Destination]-Forearm_Down[Destination])+5);

delay(Delay);

servo4.slowmove (Claw_Open, speed);

delay(Delay);

servo2.slowmove (Arm_Up[Destination], speed);
servo3.slowmove (Forearm_Up[Destination], speed+5);

delay(Delay);

servo1.slowmove (90, speed);
servo2.slowmove (46, speed);
servo3.slowmove (100, speed);

delay(1000);
digitalWrite(pinT, LOW);

}




void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  pinMode(pinT, OUTPUT);
  pinMode(pin1, INPUT_PULLUP);

   
  //Attaching the servos to pins:
  servo1.write(90);
  servo2.write(46);
  servo3.write(100);
  servo4.write(85);
  
  
  servo1.attach(6);
  servo2.attach(9);
  servo3.attach(10);
  servo4.attach(11);
}

void loop() {
  // Check if data is available in the Serial Monitor
  digitalWrite(pinT, LOW);
  Serial.println("1");
  if (Serial.available() > 0) {
    digitalWrite(pinT, LOW);
    // 2. Read the first number (Origin)
    // parseInt skips leading whitespace, so it handles the start well.
    int originSquare = Serial.parseInt();

    // 3. ROBUST WAIT for the second number (Destination)
    // This loop discards spaces/newlines until it finds a strict DIGIT (0-9).
    // This prevents the "Move to 0" error caused by the Enter key.
    while (true) {
      digitalWrite(pinT, LOW);
      // If buffer is empty, wait for user input
      while (Serial.available() == 0) {
        // Do nothing, just wait for data
      }
      
      // Look at the next character WITHOUT removing it yet
      char incoming = Serial.peek();
      
      // If it is a digit, we are ready to parse! Break the wait loop.
      if (isDigit(incoming)) {
        break; 
      }
      
      // If it's NOT a digit (like a newline or space), throw it away and keep waiting
      Serial.read(); 
    }

    // 4. Read the second number
    int destinationSquare = Serial.parseInt();

    // 5. Clear the buffer 
    // (Throw away the newline after the second number so it doesn't trigger the loop again)
    while (Serial.available() > 0) {
      Serial.read();
    }

    // 6. Execute Valid Move
    // (You can add a check here: if origin is 0 and dest is 0, maybe don't move?)
    Serial.print("Executing Move: ");
    Serial.print(originSquare);
    Serial.print(" to ");
    Serial.println(destinationSquare);
      
    Move(originSquare, destinationSquare);
  }

}