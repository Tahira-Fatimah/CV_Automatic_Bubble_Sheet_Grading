from imutils.perspective import four_point_transform
from imutils import contours
import numpy as np
import imutils
import cv2
import argparse
import os


def calculate_threshold(radius):
    return 38.89 * radius - 180.57


ANSWER_KEY = {
    0: 1, 1: 3, 2: 1, 3: 0, 4: 2, 5: 0, 6: 0, 7:0, 8:0, 9:0
}

# image_path = "omr_test_01-3.png" 
parser = argparse.ArgumentParser(description="Process OMR image for answer detection.")
parser.add_argument("image_path", help="Path to the image file to process", type=str)
args = parser.parse_args()

# Use the provided image path
image_path = args.image_path
image = cv2.imread(image_path)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
edged = cv2.Canny(blurred, 75, 200)

cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
docCnt = None

if len(cnts) > 0:
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        # if our approximated contour has four points, then we assume we've found the paper
        if len(approx) == 4:
            docCnt = approx
            break

paper = four_point_transform(image, docCnt.reshape(4, 2))
warped = four_point_transform(gray, docCnt.reshape(4, 2))

# apply Otsu's thresholding method to binarize the warped paper
thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

# find contours in the thresholded image
cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)

questionCnts = []
circles_radius = []
for c in cnts:
    (x, y, w, h) = cv2.boundingRect(c)
    ar = w / float(h)
    # identfying bubbles on the basis of aspect ratio, the aspect ratio of circles is approximately 1
    if w >= 14 and h >= 14 and ar >= 0.8 and ar <= 1.2:
        circles_radius.append((w/2 + h/2)/2) 
        questionCnts.append((c, (x, y, w, h)))

mean_radius = np.mean(circles_radius)
FILL_THRESHOLD = calculate_threshold(mean_radius)

questionCnts = sorted(questionCnts, key = lambda item : item[1][1]) #sort on the basis of y position of all contours (firs 4/5 values would be the bubbles at the top of the sheet and so on)
correct = 0
score = 0
answers_per_question = max(len(questionCnts) // len(ANSWER_KEY), 1)

for (question_number, i) in enumerate(np.arange(0, len(questionCnts), answers_per_question)):
    contours_of_one_question_in_row = sorted(questionCnts[i: i+ answers_per_question], key = lambda item : item[1][0]) #sort on the basis of x position of the first Answer_per_question contours 
    contours_of_one_question_in_row = [item[0] for item in contours_of_one_question_in_row] #get only the contour, discarding the boundingRect values 
    bubbled = None

    filled_circles_count = 0 
    
    for (contour_index, contour) in enumerate(contours_of_one_question_in_row):
        mask = np.zeros(thresh.shape, dtype="uint8") # make zero mask of binary image size
        cv2.drawContours(mask, [contour], -1, 255, -1) # draw only the current detected contour on the binary thresholded image
        mask = cv2.bitwise_and(thresh, thresh, mask=mask) # take bitwise and of the bin image(mask) obtained in previous step and the original bin image
        # what this would do is, it would give only white pixels on the area that overlaps with the filled bubble
        total = cv2.countNonZero(mask) 
        #count 1s, the more 1s the more chances of the bubble being filled
        if total >= FILL_THRESHOLD:
            filled_circles_count += 1
            
        if bubbled is None or total > bubbled[0]:
            bubbled = (total, contour_index)


    color = (0, 0, 255)  # red color for incorrect
    correct_answer_index = ANSWER_KEY.get(question_number, -1)  # Get the correct answer index from the answer key
    if filled_circles_count >= 2 :
        cv2.drawContours(paper, [contours_of_one_question_in_row[correct_answer_index]], -1, color, 3)
        score -= 0.25 # -0.25 if more than one circles filled
        continue
        
    if correct_answer_index != -1 and correct_answer_index < len(contours_of_one_question_in_row):
        if correct_answer_index == bubbled[1]:
            color = (0, 255, 0)  # Green color for correct answer
            correct += 1
            score += 1
        else:
            score -= 0.25 # -0.25 if wrong answet
        cv2.drawContours(paper, [contours_of_one_question_in_row[correct_answer_index]], -1, color, 3) #drawing contour on the original image


num_questions = len(ANSWER_KEY)
cv2.putText(paper, f"Score: {score:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
output_folder = "static/output_images"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Save the output image to the folder
output_image_path = os.path.join(output_folder, "output_image.png")
cv2.imwrite(output_image_path, paper)

print("output_image.png")

# cv2.imshow("Original", image)
# cv2.imshow("Exam", paper)
# cv2.waitKey(0)
# cv2.destroyAllWindows()