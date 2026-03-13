from fastapi import FastAPI,Path,HTTPException,Query
from fastapi.responses import JSONResponse
import json
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional


app=FastAPI(title="Patient management API",
            description='CRUD API for managing patient records with BMI calculation')

class Patient(BaseModel):
    id:Annotated[str, Field(...,description='Id of patient', examples=['P001'])]

    name:Annotated[str, Field(...,description='Name of patient')]

    city:Annotated[str, Field(..., description='City where patient is living')]

    age:Annotated[int, Field(...,gt=0,lt=120,description ='Age of patient')]

    gender:Annotated[Literal['Male', 'Female','Other'], Field(..., description='Gender of patient')]

    height:Annotated[float,Field(..., gt=0,description='Height of patient in mtr')]
                     
    weight:Annotated[float, Field(..., description='Weight of patient in kg')]

    @computed_field
    @property
    def bmi(self)->float:
        bmi=round(self.weight/(self.height**2),2)
        return bmi
    
    @computed_field
    @property
    def verdict(self)->str:
        if self.bmi<18.5:
            return 'underweight'
        elif self.bmi<25:
            return 'Normal'
        elif self.bmi<30:
            return 'overweight'
        else:
            return 'Obese'

class PatientUpdate(BaseModel):
    name:Annotated[Optional[str], Field(default=None)]
    city:Annotated[Optional[str], Field(default=None)]
    age:Annotated[Optional[int],Field(default=None,gt=0)]
    gender:Annotated[Optional[Literal['Male','Female','Other']], Field(default=None)]
    height:Annotated[Optional[float], Field(default=None, gt=0)]
    weight:Annotated[Optional[float], Field(default=None, gt=0)]    




def load_data():
    with open('patients.json','r') as f:
        data=json.load(f)
    return data    

def save_data(data):
    with open('patients.json','w') as f:
        json.dump(data, f, indent=4)


@app.get("/")
def hello():
    return {'message': 'Patient mangaement api'}

@app.get('/about')
def about():
    return{'message':'Fully fucntional API to manage your patients records'} 

@app.get('/view')
def view():
    data=load_data()
    return data

@app.get('/patient/{patient_id}')
def view_patient(patient_id:str=Path(...,description='ID of the patient in DB',examples=['P001'])):
    data=load_data()
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404,detail='Patient not found')

@app.get('/sort')
def sort_patients(sort_by:str=Query(...,description ='Sort on basis of height,weight,or bmi'),order:str=Query('asc',description='sort in asc or desc order')):

    valid_fields=['height','weight','bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail='Invalid filed select from{valid_fields}')
    
    if order not in ['asc','desc']:
        raise HTTPException(status_code=400,detail='Invalid order select between asc and desc')
    data=load_data()
    sort_order=True if order =='desc' else False
    sorted_data=sorted(data.values(),key=lambda x:x.get(sort_by,0),reverse=sort_order)
    return sorted_data

@app.post('/create')
def create_patient(patient:Patient):
    
    data=load_data() # load existing data

    #check is patient is already exist
    if patient.id in data:
        raise HTTPException(status_code=400, detail='Patient already exist')
    
    # new patient add to the db
    patient_data = patient.model_dump(exclude=['id'])
    data[patient.id] = patient_data #python dict

    #save into json file
    save_data(data)

    return JSONResponse(status_code=201,content={'message':'patient created successfully'}) 


@app.put('/edit/{patient_id}')
def update_patient(patient_id:str, patient_update: PatientUpdate):
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    existing_patient_info=data[patient_id]

    updated_patient_info=patient_update.model_dump(exclude_unset=True) #convert to dic

    existing_patient_info.update(updated_patient_info)
    #existing_patient_info-> pydentaic object -> updated bmi+verdict
    existing_patient_info['id']=patient_id
    patient_pydantic_obj=Patient(**existing_patient_info)
    #pydantic object to dict
    existing_patient_info=patient_pydantic_obj.model_dump(exclude='id')
    #add this dict to data
    data[patient_id]=existing_patient_info
    #save data
    save_data(data)

    return JSONResponse(status_code=200,content={'message':'patient updated'})
      

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id:str):
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    del data[patient_id]

    save_data(data)
    return JSONResponse(status_code=200, content={'message':'patient deleted'})

   