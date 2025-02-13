from antlr4 import *
from joiParser import joiParser
from joiVisitor import joiVisitor
import sys
from symbolTable import SymbolTable

#ytd means yet to be decided
# you'll see in some parts of code

ifqueue=[]
elseifqueue=[]
elsequeue=[]
whilequeue=[]
dowhilequeue=[]
switchqueue=[]
casequeue=[]
forqueue=[]
loopqueue=[]
BreakOrContinueWhichLoop=[] #We will push which loop this statement belongs to when we enter the loop node so that when we encounter break statement
                    # we can direclty write JMP to end_{whatever} and when we come out of the loop node, we pop from it.
                    #If it is empty, it means it is not allowed and program breaks.
ifq=0
elseifq=0
elseq=0
whileq=0
dowhileq=0
switchq=0
caseq=0
forq=0
label_counter=0
current_func_name=None
current_func_return_type=None
returnStmtFound=False
joiFuncVisited=False
# thisisaconstdeclstmt = 0

symbolTable = SymbolTable()

def ExitFromProgram(errormessage):
    print(errormessage)
    sys.exit()

class VMCodeGenerator(joiVisitor):
    def __init__(self):
        self.instructions = [] 
        self.optimised_instructions = []

    def visitProgram(self, ctx:joiParser.ProgramContext):
        global joiFuncVisited
        self.visitChildren(ctx)
        print(joiFuncVisited)
        if(not joiFuncVisited):
            self.optimised_instructions = self.instructions
        joiFuncVisited=False
        symbolTable.clear()
        return self.instructions
    
 


    def visitStatements(self, ctx:joiParser.StatementsContext):
        for statement in ctx.statement(): 
            self.visit(statement)  
            
    def visitStatement(self, ctx:joiParser.StatementContext):
        if ctx.printStmt():
            return self.visit(ctx.printStmt())
        elif ctx.inputStmt():
            return self.visit(ctx.inputStmt())
        elif ctx.assignStmt():
            return self.visit(ctx.assignStmt())
        elif ctx.classFunctionAccessStmt():
            return self.visit(ctx.classFunctionAccessStmt())
        elif ctx.declarationStmt():
            return self.visit(ctx.declarationStmt())
        elif ctx.constDeclarationStmt():
            return self.visit(ctx.constDeclarationStmt())
        elif ctx.ifStmt():
            global ifq
            ifqueue.append(ifq)
            ifq+=1
            return self.visit(ctx.ifStmt())
        elif ctx.switchStmt():
            global switchq
            switchqueue.append(switchq)
            switchq+=1
            return self.visit(ctx.switchStmt())
        elif ctx.whileStmt():
            global whileq
            whilequeue.append(whileq)
            loopqueue.append(whileq)
            whileq+=1
            return self.visit(ctx.whileStmt())
        elif ctx.doWhileStmt():
            global dowhileq
            dowhilequeue.append(dowhileq)
            loopqueue.append(dowhileq)
            dowhileq+=1
            return self.visit(ctx.doWhileStmt())
        elif ctx.forStmt():
            global forq
            forqueue.append(forq)
            loopqueue.append(forq)
            forq+=1
            return self.visit(ctx.forStmt())
        elif ctx.breakStmt():
            return self.visit(ctx.breakStmt())
        elif ctx.continueStmt():
            return self.visit(ctx.continueStmt())
        elif ctx.functionCall():
            return self.visit(ctx.functionCall())
        elif ctx.expression():
            return self.visit(ctx.expression())
        elif ctx.deleteStmt():
            return self.visit(ctx.deleteStmt())
        elif ctx.tryCatchStmt():
            return self.visit(ctx.tryCatchStmt())
        elif ctx.throwStmt():
            return self.visit(ctx.throwStmt())
        elif ctx.objectDeclarationStmt():
            return self.visit(ctx.objectDeclarationStmt())
        elif ctx.structDeclarationStmt():
            return self.visit(ctx.structDeclarationStmt())
        elif ctx.enumDeclarationStmt():
            return self.visit(ctx.enumDeclarationStmt())
        elif ctx.returnStmt():
            return self.visit(ctx.returnStmt())
        



    def visitInputStmt(self, ctx: joiParser.InputStmtContext):
        var_info = self.visit(ctx.idOrPointerOrAddrId())
        var_name = var_info[1]
        var_type = var_info[0]
        if(not symbolTable.read(var_name)):
            ExitFromProgram(f'cannot take input for undeclared variable {var_name}')
        if(var_type=='address_identifier'):
            ExitFromProgram(f'cannot take input into a referenced variable {var_name}')
        # self.instructions.append(f'INPUT {var_name}')
        self.instructions.append(f'scan local {symbolTable.read(var_name)["id"]} {symbolTable.read(var_name)["datatype"].upper()}')

    
    def visitDeleteStmt(self, ctx: joiParser.DeleteStmtContext):
        var_info = self.visit(ctx.idOrPointerOrAddrId())
        var_name = var_info[1]
        var_type = var_info[0]
        if(not symbolTable.read(var_name)):
            ExitFromProgram(f'cannot delete undeclared variable {var_name}')
        if((symbolTable.read(var_name))['type']!='pointer'):
            ExitFromProgram(f'please provide a pointer to delete')
        self.instructions.append(f'delete {symbolTable.read(var_name)["type"]} {symbolTable.read(var_name)["id"]} {symbolTable.read(var_name)["datatype"]}')#I exactly dont know, just put it here as of now
        symbolTable.delete(var_name)
        
    ##No VM for this.. because nothing came from their side.. and I don't know how exactly they want it.. We might not even need this
    def visitReferenceDeclarationStmt(self, ctx: joiParser.ReferenceDeclarationStmtContext):
        data_type = ctx.dataType().getText()
        var_name = self.visit(ctx.address_identifier())[1]
        if(symbolTable.read(var_name)):
            ExitFromProgram(f'already declared {var_name}. cannot reference declare it.')

        referenced_info = self.visit(ctx.idOrPointerOrAddrId())#[type, name]
        referenced_name = referenced_info[1]
        referenced_type = referenced_info[0] #pointer or address or variable
        if(referenced_type=='address_identifier'):
            ExitFromProgram(f'cannot bind {referenced_name} to {var_name}')

        data_type_of_referenced_var = symbolTable.read(referenced_name)['datatype']
        if(data_type_of_referenced_var!=data_type):
            ExitFromProgram(f'cannot bind address of {data_type_of_referenced_var} {referenced_name} to {data_type} {var_name}')
        
        symbolTable.create(name=var_name, symbol_type='reference',scope='ytd',datatype=data_type)
        for expr in ctx.expression():
            self.visit(expr)

    
    def visitClassDef(self, ctx: joiParser.ClassDefContext):
        class_name = ctx.IDENTIFIER(0).getText()
        if symbolTable.read(class_name):
            ExitFromProgram(f"Class '{class_name}' already defined.")
        symbolTable.create(name=class_name, symbol_type='class', scope='ytd')
        self.instructions.append(f'declare CLASS {class_name}')

        access_specifier = None
        for item in ctx.children: 
            if isinstance(item, joiParser.AccessSpecifierContext):
                access_specifier = item.getText().upper()
            elif isinstance(item, joiParser.DeclarationStmtContext):
                if access_specifier:
                    self.instructions.append(f'ACCESS {access_specifier} BEGIN')
                self.visitDeclarationStmt(item)
                if access_specifier:
                    self.instructions.append(f'ACCESS {access_specifier} END')
            elif isinstance(item, joiParser.FunctionDefContext):
                if access_specifier:
                    self.instructions.append(f'ACCESS {access_specifier} BEGIN')
                self.visitFunctionDef(item)
                if access_specifier:
                    self.instructions.append(f'ACCESS {access_specifier} END')
            elif isinstance(item, joiParser.ConstructorContext):
                if access_specifier:
                    self.instructions.append(f'ACCESS {access_specifier} BEGIN')
                self.visitConstructor(item)
                if access_specifier:
                    self.instructions.append(f'ACCESS {access_specifier} END')
            # else:
            #     print(f"Unknown class member type: {type(item)}")

        self.instructions.append(f'end CLASS {class_name}')

    def visitConstructor(self, ctx: joiParser.ConstructorContext):
        constructor_name = ctx.IDENTIFIER().getText()

        if not symbolTable.read(constructor_name) or symbolTable.read(constructor_name)['type'] != 'class':
            ExitFromProgram(f"{constructor_name} is not a valid constructor or does not match any class name.")

        self.instructions.append(f'CONSTRUCTOR_{constructor_name}:')

        symbolTable.create(name=constructor_name, symbol_type='constructor', scope='ytd')
        if ctx.paramList():
            self.instructions.append(f'PARAMS START')
            params, params_data_types = self.visitParamList(ctx.paramList())
            for param in params:
                self.instructions.append(f'PARAM {param}')
            self.instructions.append(f'PARAMS END')

        if ctx.statements():
            self.visit(ctx.statements())
        self.instructions.append('END_CONSTRUCTOR')


    
    def visitObjectDeclarationStmt(self, ctx: joiParser.ObjectDeclarationStmtContext):
        class_name = ctx.IDENTIFIER(0).getText()
        object_name = ctx.IDENTIFIER(1).getText()
        constructor_name = ctx.IDENTIFIER(2).getText()
        if(symbolTable.read(object_name)):
            ExitFromProgram(f'already declared {object_name}. use another name.')
        if(not symbolTable.read(class_name) or not symbolTable.read(constructor_name)):
            ExitFromProgram(f'{class_name} or {constructor_name} is not declared yet. Please check')
        if((symbolTable.read(class_name))['type']!='class' or (symbolTable.read(constructor_name))['type']!='class'):
            ExitFromProgram(f'{class_name} or {constructor_name} is not a class. cannot make a object')
        symbolTable.create(name=object_name, symbol_type='object',scope='ytd', datatype=class_name)
        self.instructions.append(f'DECLARE {class_name} {object_name}')
        if(ctx.expression()):
            self.instructions.append(f'ARGS_for_CNSTRCTR') # still need to write upward push for expression results
            for expr in ctx.expression():
                self.visit(expr)
            self.instructions.append(f'ARGS END')
        
    def visitClassFunctionAccessStmt(self, ctx: joiParser.ClassFunctionAccessStmtContext):
        object_name = ctx.IDENTIFIER().getText()
        if(not symbolTable.read(object_name) or symbolTable.read(object_name)['type']!='object'):
            ExitFromProgram(f'There is no such object as {object_name}. Please check')
        self.visitFunctionCall(ctx.functionCall())
        
        
    def visitConstDeclarationStmt(self, ctx: joiParser.ConstDeclarationStmtContext):
        # global thisisaconstdeclstmt
        # thisisaconstdeclstmt = 1
        variables = self.visit(ctx.declarationStmt())
        # self.instructions.append(f"PREVIOUS {len(variables)} DECLARES ARE CONSTANT")
        for var in variables:
            symbolTable.update(name=var[1], constant=True)
        # thisisaconstdeclstmt = 0
        
    def visitBreakStmt(self, ctx: joiParser.BreakStmtContext):
        if(BreakOrContinueWhichLoop):
            self.instructions.append(f'goto end_{BreakOrContinueWhichLoop[-1]}')
        else:
            ExitFromProgram("break written outside loop")
            pass # this is the case where break is not written in any loop but outside the loop.. we have to halt the 
                # code here. HOW DO WE DO THAT???

    def visitContinueStmt(self, ctx: joiParser.ContinueStmtContext):
        if(BreakOrContinueWhichLoop):
            self.instructions.append(f'goto {BreakOrContinueWhichLoop[-1]}')
        else:
            ExitFromProgram("continue written outside loop")
            pass # this is the case where continue is not written in any loop but outside the loop.. we have to halt the 
                # code here. HOW DO WE DO THAT???
        
    def visitPrintStmt(self, ctx: joiParser.PrintStmtContext):
        to_be_printed_string=""
        for printexpression in ctx.printExpressionList():
            data_to_print, data_type_of_the_print = self.visit(printexpression)
            # to_be_printed_string+=data_to_print ##if we want the whole statement else
            to_be_printed_string = data_to_print
            self.instructions.append(f'push data {to_be_printed_string} {data_type_of_the_print.upper()}')
    
    def visitPrintExpressionList(self, ctx: joiParser.PrintExpressionListContext):
        if(ctx.expression()):            
            value_of_expression, data_type_of_expression = self.visit(ctx.expression()) #value of the expression doesn't calculate the final answer.. for strings this might work but for variable and stuff we have to think with VM team
            ## for arithmetic expressions i am now returning only the first variable in arithmetic expression I don't have a choice.. need to work with VM team to exactly ask how they need... what is the VM code to print statement
            return value_of_expression, data_type_of_expression
            ##above can be easily written as return self.visit(ctx.expression())
            ##but wrote like this for more clarity
        
        if(ctx.ENDL()):
            return "\\n", "str"
        
        return "", "str"
    
    def visitFunctionDef(self, ctx: joiParser.FunctionDefContext):
        global current_func_name, current_func_return_type, returnStmtFound
        return_type="void"
        if(ctx.dataType()):#talks about which return type the function is
            return_type = ctx.dataType().getText() 
        func_name = ctx.IDENTIFIER().getText()
        if(symbolTable.read(func_name) and symbolTable.read(func_name)['functiondefined']==True):
            ExitFromProgram(f"The function {func_name} already exists. Use a different name.")
        # self.instructions.append(f'FUNC_{func_name}:') #check if func already exists
        
        params_data_type_array = []
        params=[]
        if(ctx.paramList()):# get info about paramnames and their datatypes to check for argument passing
            params, params_data_type_array = self.visitParamList(ctx.paramList()) 

        self.instructions.append(f'function {func_name} {len(params_data_type_array)} {return_type.upper()}')
        
        if(ctx.COLON()):##This case is for when function is declared and defined here
            if(symbolTable.read(func_name)):
                symbolTable.update(name=func_name, functiondefined=True)
            else:
                symbolTable.create(name=func_name, symbol_type='function', scope='ytd', returntype=return_type, paramstype=params_data_type_array, functiondefined=True)
            for i, param in enumerate(params):
                self.instructions.append(f'push argument {param} {params_data_type_array[i]}')

            if(ctx.statements()):#casual statements
                current_func_name = func_name
                current_func_return_type = return_type
                self.visit(ctx.statements())
                # if(ctx.returnStmt()):
                #     varname_func_returns, data_type_func_returns = self.visit(ctx.returnStmt())
                #     #if both are None that means it should match with void function
                #     if(return_type=="void" and data_type_func_returns!=None):
                #         ExitFromProgram(f'You cannot return anything for a void function')

                #     #we know that returntype of func must match with the return statement data type
                #     if(return_type!=data_type_func_returns):
                #         ExitFromProgram(f'function {func_name} should return {return_type.upper()}, but you are returning {data_type_func_returns}')
                
                # else: #there is no return statement, this is acceptable only if return type is void.. if return type is not void then throw error
                #     if(return_type!="void"):
                #         ExitFromProgram(f'function {func_name} must return {return_type.upper()} type. Currently you are returning nothing')
            if(return_type!='void' and not returnStmtFound):
                ExitFromProgram(f'function {func_name} must return {return_type.upper()} type. Currently you are returning nothing')
            returnStmtFound = False
            # self.instructions.append('return')#this appears only when it is defined not when it is declared
            if(return_type=='void'):
                self.instructions.append('return')
        else: #func is declared here.. but the definition is in someother file
            symbolTable.create(name=func_name, symbol_type='function', scope='ytd', returntype=return_type, paramstype=params_data_type_array, functiondefined=False)
            self.instructions.append('return_') #this return statement helps us in code optimisation.. so this is useless for VM but for compiler optimisatino it has so much use.
            

        current_func_name = 'joi'
        current_func_return_type = 'int'
        
        # if(return_type=='void'):
        #     self.instructions.append('return VOID')
        # else:
        #     self.instructions.append(f'return {func_name}')

    def visitParamList(self, ctx: joiParser.ParamListContext):
        params = []
        params_data_types = []
        for param in ctx.param():
            param_name, param_data_type, param_type = self.visit(param)
            params.append(param_name)
            params_data_types.append(param_data_type)
        return params, params_data_types
    
    def visitParam(self, ctx: joiParser.ParamContext):#need to add scope when adding to symbol table
        if(ctx.dataType()):
            data_type = ctx.dataType().getText()
        param_info = [None, None]

        param_info = self.visit(ctx.idOrPointerOrAddrId())
        param_name = param_info[1]
        param_type = param_info[0]

        if(symbolTable.read(param_name)):# need to implement scope for this.. as of now only name checking is done
            ExitFromProgram("param name is already used in the code. Try different name.")
        symbolTable.create(name=param_name, symbol_type='parameter', scope='ytd',datatype=data_type)
        return param_name, data_type, param_type
    
    def visitFunctionCall(self, ctx: joiParser.FunctionCallContext):
        
        # if(len(ctx.IDENTIFIER())==1):
            
        func_name = ctx.IDENTIFIER().getText()
        if(not symbolTable.read(func_name)):
            ExitFromProgram(f"No such function to call {func_name}")
        
        # Arguments in a function call
        arguments_data_types = []
        arguments=[]
        if(ctx.argList()):
            # self.instructions.append(f'ARGS_START')
            arguments, arguments_data_types = self.visit(ctx.argList())
            # self.instructions.append(f'ARGS END')
        
        function_info = symbolTable.read(func_name)
        function_return_type = function_info['returntype']
        function_params_type = function_info['paramstype']

        #the arguments' datatypes should match with the function's params datatypes else throw error
        if(function_params_type!=arguments_data_types):
            ExitFromProgram(f'The arguments and parameters are not matching for the function {func_name}')

        self.instructions.append(f'call {func_name} {len(arguments)}')
        symbolTable.update(name=func_name, functioncalled=True)
        return func_name, function_return_type

    
    def visitArgList(self, ctx: joiParser.ArgListContext):
        arguments = []
        arguments_data_types = []
        for argum in ctx.expression():
            argum_name, argum_data_type = self.visit(argum)
            arguments.append(argum_name)
            arguments_data_types.append(argum_data_type)
        return arguments, arguments_data_types


    def visitReferenceDataType(self, ctx: joiParser.ReferenceDataTypeContext):
        return ctx.getChild(0).getText()

    def visitDeclarationStmt(self, ctx: joiParser.DeclarationStmtContext):
        # global thisisaconstdeclstmt
        # constantText="local"
        # if(thisisaconstdeclstmt==1):
        #     constantText = "constant"
        if ctx.dataType() and ctx.varList():
            data_type = ctx.dataType(0).getText()  
            var_list = ctx.varList() 
            variables = self.visit(var_list) ##variabletype(var\pointer\address) , varname
           
            if not ctx.NEW() and ctx.expression():  
                var_name, var_data_type = self.visit(ctx.expression())  
                for var in variables:
                    if(symbolTable.read(var[1])):# if the variable is already declared somewhere.. doesn't matter if it is var or func or array. once declared cannot be used again
                        ExitFromProgram(f'already declared {var[1]} variable')

                    if(data_type!='char' and data_type!='str' and data_type!=var_data_type): # prevents int a = 'c';
                        ExitFromProgram(f'Cannot assign {var_data_type} to {data_type}')
                    # self.instructions.append(f'DECLARE {var[1]} {data_type}')  # Declaration
                    # self.instructions.append(f'STORE {var[1]}') # Store initialized value
                    # self.instructions.append(f'POP {var[1]}') # since it is only declaration you can take it out.
                    symbolTable.create(name=var[1], symbol_type=var[0], scope='ytd', datatype=data_type, value='ytd') # we don't know how to get expression value to put it here
                    # self.instructions.append(f'push local {symbolTable.read(var[1])["id"]} {data_type}')  # Declaration
                    # self.instructions.append(f'STORE {var[1]}') # Store initialized value
                    self.instructions.append(f'pop local {symbolTable.read(var[1])["id"]} {data_type.upper()}') # since it is only declaration you can take it out.
                    
            elif ctx.NEW():
                for var in variables:
                    if(symbolTable.read(var[1])):# if the variable is already declared somewhere.. doesn't matter if it is var or func or array. once declared cannot be used again
                        ExitFromProgram(f'already declared {var[1]} variable')
                    
                    # this is for stmts like int$ a = new int;
                    # so it should not allow like int$ a = new bool;
                    #for that is the below check
                    if(ctx.dataType(1).getText()!=data_type):
                        ExitFromProgram(f'Cannot create new {ctx.dataType(1).getText()} for {var[1]} which is {data_type}')

                    if(var[0]!='pointer'):
                        ExitFromProgram(f'cannot declare new {data_type} to {var[1]}.\n {var[1]} is not a pointer')

                    # self.instructions.append(f'DECLARE NEW {var[1]} {data_type}')   
                    symbolTable.create(name=var[1], symbol_type=var[0], scope='ytd', datatype=data_type)
                    self.instructions.append(f'alloc {data_type}')
                    # self.instructions.append(f'push local {symbolTable.read(var[1])["id"]} {data_type} new')    
                    self.instructions.append(f'pop local {symbolTable.read(var[1])["id"]} ptr')

            else:# int a;
                for var in variables:
                    if(symbolTable.read(var[1])):# if the variable is already declared somewhere.. doesn't matter if it is var or func or array. once declared cannot be used again
                        ExitFromProgram(f'already declared {var[1]} variable')
                    # self.instructions.append(f'DECLARE {data_type} {var[1]}')  # Just declare if no assignment
                    symbolTable.create(name=var[1], symbol_type=var[0], scope='ytd', datatype=data_type)
                    #no default values for these statements..
                    # self.instructions.append(f'push local {symbolTable.read(var[1])["id"]} {data_type}')  # Just declare if no assignment
                    self.instructions.append(f'pop local {symbolTable.read(var[1])["id"]} {data_type}')  # Just declare if no assignment

            return variables
        elif(ctx.arrayDeclarationStmt()):
            return self.visit(ctx.arrayDeclarationStmt())
        else:
            raise Exception("Unhandled declaration statement type")
    
    def visitArrayDeclarationStmt(self, ctx: joiParser.ArrayDeclarationStmtContext):
        
        data_type_of_array = ctx.dataType().getText()  
        arrayinfo = self.visit(ctx.idOrPointerOrAddrId())
        arrayName = arrayinfo[1] 
        if(symbolTable.read(arrayName)):# if the variable is already declared somewhere.. doesn't matter if it is var or func or array. once declared cannot be used again
            ExitFromProgram(f'already declared {arrayName} variable')
        if(arrayinfo[0]=='address_identifier'):
            ExitFromProgram(f'cannot create {arrayName} array of references')

        symbolTable.create(name=arrayName, symbol_type='array', scope='ytd', datatype=data_type_of_array)
        
        ##THis part is for array size during its declaration
        # self.instructions.append(f'SIZE OF ARRAY START')
        for expression in ctx.expression():
            index, index_data_type = self.visit(expression) #index data tyep cannot be anything other than int
            if(index_data_type!='int'):
                ExitFromProgram(f'array cannot be accessed with {index_data_type} in []. Please use integers') 
            self.instructions.append(f'alloc {index} {index_data_type}')
        # self.instructions.append(f'SIZE OF ARRAY END')

        ##Here the initial values are assigned.
        if(ctx.arrayValueAssigning()):
            values, data_type_of_initial_values = self.visit(ctx.arrayValueAssigning())
            if(data_type_of_initial_values!='char' and data_type_of_initial_values!='str' and data_type_of_initial_values!=data_type_of_array):
                ExitFromProgram(f'Cannot assign {data_type_of_initial_values} to {data_type_of_array}')

        # self.instructions.append(f'DECLARE {data_type_of_array} ARRAY {arrayName} of {arrayinfo[0]}') 
        self.instructions.append(f'pop local {symbolTable.read(arrayName)["id"]} ptr')  
             
        return [['array', arrayName]]#This line is useful for const declarations.. don't think it is useless


    def visitArrayValueAssigning(self, ctx: joiParser.ArrayValueAssigningContext):
        if(ctx.expression()):
            return self.visit(ctx.expression()) ## returns in the format.. value, datatype ## just like other returns
        
        set_of_data_types = set()
        for assigning in ctx.arrayValueAssigning():
            assigning_value_not_needed_really, assigning_value_data_type = self.visit(assigning)
            set_of_data_types.add(assigning_value_data_type)
            ##some big jugaad... first let's push all the datatype returns into one set.
            ##if set size is more than one then it means there are more than one datatypes in the values.. not allowed.
            ##if set size is one then we push it back to arrayDeclarationStmt and check if datatype of declaration is matching with these values datatypes...
            ##one check is enough.. since previously we already checked if all values are same datatype
            ## this works no issues

        if(len(set_of_data_types)>1):#this means more than one datatype is in the array we cannot declare like that
            ExitFromProgram(f'Cannot declare an array with values of different data types')
        
        return "", set_of_data_types.pop()

    def visitVarList(self, ctx:joiParser.VarListContext):
        variables = []
        for var in ctx.var():
            variables.append(self.visit(var))
        return variables
    
    def visitVar(self, ctx: joiParser.VarContext):
        return self.visit(ctx.idOrPointerOrAddrId())
    
    def visitPointer(self, ctx: joiParser.PointerContext):
        varname = self.visit(ctx.idOrPointerOrAddrId())[1]
        return ['pointer', varname]
    
    def visitAddress_identifier(self, ctx: joiParser.Address_identifierContext):
        varname = ctx.IDENTIFIER().getText()
        return ['address_identifier', varname]

    def visitExpression(self, ctx:joiParser.ExpressionContext):
        if(ctx.typecastExpr()):
            return self.visit(ctx.typecastExpr())
        if(ctx.logicalOrExpression()):
            return self.visit(ctx.logicalOrExpression())

    def visitLogicalOrExpression(self, ctx:joiParser.LogicalOrExpressionContext):
        first_loc, data_type_of_first_loc = self.visit(ctx.logicalAndExpression(0))

        for i in range(1, len(ctx.logicalAndExpression())):
            next_loc, data_type_of_next_loc = self.visit(ctx.logicalAndExpression(i)) 
            self.instructions.append('or') 
            data_type_of_first_loc = 'bool'

        return first_loc, data_type_of_first_loc
            
    def visitLogicalAndExpression(self, ctx:joiParser.LogicalAndExpressionContext):
        first_lac, data_type_of_first_lac = self.visit(ctx.rel_expr(0))

        for i in range(1, len(ctx.rel_expr())):
            next_lac, data_type_of_next_lac = self.visit(ctx.rel_expr(i))  
            self.instructions.append('and') 
            data_type_of_first_lac = 'bool'

        # print(data_type_of_first_lac)
        return first_lac, data_type_of_first_lac

    def visitRel_expr(self, ctx:joiParser.Rel_exprContext):#wil always return bool
        # NOT rel_expr 
        if ctx.NOT():
            relexp, data_type_of_relexp = self.visit(ctx.rel_expr())  
            self.instructions.append('not')  
            return relexp, 'bool'
        else:
            first_expr, data_type_of_first_expr= self.visit(ctx.expr(0))
            
            for i in range(1, len(ctx.expr())):
                next_expr, data_type_of_next_expr = self.visit(ctx.expr(i))  
                comp_op = ctx.comparisonOp(i - 1).getText() 
                operation = self.visitComparisonOp(comp_op)
                # if(data_type_of_first_expr=='str' or data_type_of_next_expr=='str'):
                #     ExitFromProgram(f'Cannot operate {operation} on {first_expr}, {next_expr} strings')
                # if(data_type_of_first_expr!=data_type_of_next_expr):
                #     ExitFromProgram(f'Cannot operate {operation} on two different datatypes - {first_expr} is {data_type_of_first_expr} and {next_expr} is {data_type_of_next_expr}')
                data_type_of_first_expr = 'bool'

            # print(first_expr)
            return first_expr, data_type_of_first_expr

    def visitExpr(self, ctx:joiParser.ExprContext):
        first_term, data_type_of_first_term = self.visit(ctx.term(0)) 
        
        for i in range(1, len(ctx.term())):
            next_term, data_type_of_next_term = self.visit(ctx.term(i)) 
            op = ctx.getChild(2 * i - 1).getText()   
            if op == '+':
                operation = 'add'
            elif op == '-':
                operation = 'sub'
            self.instructions.append(operation) 
            # if(data_type_of_first_term!='int' and data_type_of_first_term!='float'):
            #     ExitFromProgram(f'Cannot operate {operation} on {first_term} which is {data_type_of_first_term}')
            # if(data_type_of_first_term!=data_type_of_next_term):
            #     ExitFromProgram(f'Cannot operate {operation} on two different datatypes - {first_term} is {data_type_of_first_term} and {next_term} is {data_type_of_next_term}')

        return first_term, data_type_of_first_term

    def visitTerm(self, ctx:joiParser.TermContext):
        first_factor, data_type_of_first_factor = self.visit(ctx.factor(0))  

        for i in range(1, len(ctx.factor())):
            next_factor, data_type_of_next_factor = self.visit(ctx.factor(i)) 
            op = ctx.getChild(2 * i - 1).getText()  
            if op == '*':
                operation = 'mul'
            elif op == '/':
                operation = 'div'
            elif op == '%':
                operation = 'mod'            
            self.instructions.append(operation)
            
            # if(data_type_of_first_factor!='int' and data_type_of_first_factor!='float'):
            #     ExitFromProgram(f'Cannot operate {operation} on {first_factor} which is {data_type_of_first_factor}')
            # if(data_type_of_first_factor!=data_type_of_next_factor):
            #     ExitFromProgram(f'Cannot operate {operation} on two different datatypes - {first_factor} is {data_type_of_first_factor} and {next_factor} is {data_type_of_next_factor}')
        

        return first_factor, data_type_of_first_factor

    def visitIdOrPointerOrAddrId(self, ctx: joiParser.IdOrPointerOrAddrIdContext):
        if(ctx.pointer()):
            return self.visit(ctx.pointer())
        elif(ctx.address_identifier()):
            return self.visit(ctx.address_identifier())
        return ['variable', ctx.IDENTIFIER().getText()]

    def visitFactor(self, ctx:joiParser.FactorContext):
        if ctx.idOrPointerOrAddrId():
            var_info = self.visit(ctx.idOrPointerOrAddrId())
            var_name = var_info[1]
            if(not symbolTable.read(var_name)):
                ExitFromProgram("cannot use undeclared variable")

            data_type_of_var_name = symbolTable.read(var_name)['datatype']
            id_of_var_name = symbolTable.read(var_name)["id"]
            if ctx.INC():
                # if(data_type_of_var_name != 'int' and data_type_of_var_name != 'float'): #we are not incrmeenting char, usually it is done in c++
                #     ExitFromProgram(f'cannot Increment a {data_type_of_var_name}')
                if(ctx.getChild(0).getText() == '++'):  # pre-increment
                    self.instructions.append(f'push local {id_of_var_name} {data_type_of_var_name.upper()}')
                    self.instructions.append('push constant 1 INT')
                    self.instructions.append('add')
                    self.instructions.append(f'pop local {id_of_var_name} {data_type_of_var_name.upper()}')
                else: #post-increment # the jugaad is to increase the value but not use it for operations. see below
                    self.instructions.append(f'push local {id_of_var_name} {data_type_of_var_name.upper()}')
                    self.instructions.append('push constant 1 INT')
                    self.instructions.append('add')
                    self.instructions.append(f'pop local {id_of_var_name} {data_type_of_var_name.upper()}') ##same like pre-incrment now var is var+1 and is stored
                    # now we subtract it by 1
                    self.instructions.append('push constant 1 INT')
                    self.instructions.append('sub')
                    #now we have (var+1)-1 = var in the stack which can be used for the operations...
                    # so we increased var but did not use it instead we used the previous version for operations
                    # and stored the new version

            elif ctx.DEC():
                # if(data_type_of_var_name != 'int' and data_type_of_var_name != 'float'): #we are not incrmeenting char, usually it is done in c++
                #     ExitFromProgram(f'cannot Decrement a {data_type_of_var_name}')
                if(ctx.getChild(0).getText() == '--'):  # pre-decrement
                    self.instructions.append(f'push local {id_of_var_name} {data_type_of_var_name.upper()}')
                    self.instructions.append('push constant 1 INT')
                    self.instructions.append('sub')
                    self.instructions.append(f'pop local {id_of_var_name} {data_type_of_var_name.upper()}')
                else: #post-decrement # the jugaad is to decrease the value but not use it for operations. see below
                    self.instructions.append(f'push local {id_of_var_name} {data_type_of_var_name.upper()}')
                    self.instructions.append('push constant 1 INT')
                    self.instructions.append('sub')
                    self.instructions.append(f'pop local {id_of_var_name} {data_type_of_var_name.upper()}') ##same like pre-decrment now var is var-1 and is stored
                    # now we add 1 to it
                    self.instructions.append('push constant 1 INT')
                    self.instructions.append('add')
                    # now we have (var-1)+1 = var in the stack which can be used for the operations...
                    # so we decreased var but did not use it instead we used the previous version for operations
                    # and stored the new version

            ## this is how we can make post increment and decrement work without any problem.. 
            # as wanted old value is used for current operation and new value is already with us to use for next operation
            
            elif ctx.expr():  
                # self.instructions.append(f'push local {id_of_var_name} {data_type_of_var_name}')  # should check this----------------
                self.instructions.append(f'push local {id_of_var_name} ptr')  # should check this----------------
                # self.instructions.append(f'ARR_INDEX START')
                for expr in ctx.expr():  
                    expr_value, expr_data_type = self.visit(expr)
                    if(expr_data_type!='int'):
                        ExitFromProgram(f'array cannot be accessed with {expr_data_type} in []. Please use integers')
                    
                # self.instructions.append(f'ARR_INDEX END')
                self.instructions.append(f'getindex')
                self.instructions.append(f'access {data_type_of_var_name}')
            else:
                self.instructions.append(f'push local {id_of_var_name} {data_type_of_var_name.upper()}')  
            return var_name, data_type_of_var_name
        elif ctx.NUMBER():
            number = ctx.NUMBER().getText()
            data_type = 'int'
            if('.' in number):
                data_type = 'float'
            self.instructions.append(f'push constant {number} {data_type.upper()}')  
            return number, data_type # value, and type
        elif ctx.STRING():
            string_value = ctx.STRING().getText()
            self.instructions.append(f'push constant {string_value} STR')  
            return string_value, 'str'
        elif ctx.CHAR_LITERAL():
            char_value = ctx.CHAR_LITERAL().getText()
            self.instructions.append(f'push constant {char_value} CHAR')  
            return char_value, 'char'
        elif ctx.TRUE():
            self.instructions.append('push constant 1 BOOL') #might have to write int instead of bool here
            return True, 'bool' 
        elif ctx.FALSE():
            self.instructions.append('push constant 0 BOOL') 
            return False, 'bool' 
        elif ctx.expr(): 
            return self.visit(ctx.expr(0))  
        elif ctx.functionCall():
            func_name, function_return_type = self.visit(ctx.functionCall()) 
            return func_name, function_return_type
        elif ctx.structAccessStmt():
            struct_var_name, struct_var_member = self.visit(ctx.structAccessStmt())
            data_type_of_member = symbolTable.read(struct_var_member)['datatype']
            return struct_var_member, data_type_of_member
        elif ctx.structAccessForArrayStmt():
            return self.visit(ctx.structAccessForArrayStmt())
        elif ctx.classFunctionAccessStmt():
            return self.visitClassFunctionAccessStmt()

    def visitStructAccessForArrayStmt(self, ctx: joiParser.StructAccessForArrayStmtContext):
        total_expressions = len(ctx.expression())
        self.instructions.append(f'ARR_INDEX START')
        for i in range(0, total_expressions):
            index, index_data_type = self.visit(ctx.expression(i))
            if(index_data_type!='int'):
                ExitFromProgram(f'array cannot be accessed with {index_data_type} in []. Please use integers') 
        self.instructions.append(f'ARR_INDEX END')
        struct_var_name, struct_var_member = self.visit(ctx.structAccessStmt())
        return struct_var_member, symbolTable.read(struct_var_member)['datatype']

    def visitTypecastExpr(self, ctx: joiParser.TypecastExprContext):
        new_data_type = ctx.dataType().getText()
        variable_to_change = ctx.IDENTIFIER().getText()
        if(not symbolTable.read(variable_to_change)):
            ExitFromProgram(f'Please declare the variable before typecasting it')
        if(symbolTable.read(variable_to_change)['datatype'] not in {'int','float','str','bool', 'char'}):
            ExitFromProgram(f'Typecasting is only done for primitive datatypes. {variable_to_change} is a {(symbolTable.read(variable_to_change))["datatype"]}')
        self.instructions.append(f'push local {symbolTable.read(variable_to_change)["id"]} {symbolTable.read(variable_to_change)["datatype"].upper()}')
        symbolTable.update(name=variable_to_change, datatype=new_data_type)
        return variable_to_change, new_data_type
    
    def visitAssignStmt(self, ctx: joiParser.AssignStmtContext):

        # if ctx.IDENTIFIER() and ctx.expression(0) and ctx.expression(1):
        # (IDENTIFIER '[' expression ']' ('[' expression ']')* '=' expression ';')
        # should check this-------------------------------------
        if ctx.idOrPointerOrAddrId() and len(ctx.expression())>=2: ## this is array case
            var_name = self.visit(ctx.idOrPointerOrAddrId())[1]  
            if(not symbolTable.read(var_name)):
                ExitFromProgram("cannot assign to undeclared array")
            if(symbolTable.read(var_name)['constant']==True):
                ExitFromProgram(f'cannot assign to constant variables')

            
            data_type_of_array = symbolTable.read(var_name)['datatype']
            id_of_array = symbolTable.read(var_name)['id']
            # index, data_type_of_index = self.visit(ctx.expression(0)) 
            # if(data_type_of_index!='int'):
            #     ExitFromProgram(f'array cannot be accessed with {data_type_of_index} in []. Please use integers') 
            
            # self.instructions.append(f'push array local {id_of_array} {data_type_of_array}') 
            self.instructions.append(f'push local {id_of_array} ptr')   
            # self.instructions.append(f'ARR_INDEX START')
            for i in range(0, len(ctx.expression()) - 1):
                index, data_type_of_index = self.visit(ctx.expression(i)) 
                if(data_type_of_index!='int'):
                    ExitFromProgram(f'array cannot be accessed with {data_type_of_index} in []. Please use integers') 
            # self.instructions.append(f'ARR_INDEX END')
            # self.instructions.append(f'push array local {id_of_array} {data_type_of_array.upper()}')  
            # self.instructions.append(f'PUSH {index}')  
            self.instructions.append(f'getindex')
            expr, data_type_of_assigning_value = self.visit(ctx.expression(len(ctx.expression())-1))  

            if(ctx.assignOp()):
                op = ctx.assignOp().getText()  
                if op == '+=':
                    self.instructions.append('add')  
                elif op == '-=':
                    self.instructions.append('sub')  
                elif op == '*=':
                    self.instructions.append('mul')  
                elif op == '/=':
                    self.instructions.append('div')
                elif op == '%=':
                    self.instructions.append('mod')
                
                if((data_type_of_array!='int' or data_type_of_assigning_value!='int') and (data_type_of_array!='float' or data_type_of_assigning_value!='float')):
                    ExitFromProgram(f'can perform {op} operation only int and floats.\n{var_name} is of {data_type_of_array} and you are trying to do {op} with {data_type_of_assigning_value}')

            if(data_type_of_array!='char' and data_type_of_array!='str' and data_type_of_array!=data_type_of_assigning_value):
                ExitFromProgram(f'Cannot assign {data_type_of_assigning_value} to {data_type_of_array}')
            # self.instructions.append(f'pop array local {id_of_array} {data_type_of_array.upper()}') 
            self.instructions.append(f'store {data_type_of_array.upper()}') 

        elif ctx.idOrPointerOrAddrId() and ctx.expression(0) and not ctx.assignOp(): # a = 3 type statements
            var_name = self.visit(ctx.idOrPointerOrAddrId())[1] 
            
            if(not symbolTable.read(var_name)):
                ExitFromProgram("cannot assign to undeclared variable") 
            if(symbolTable.read(var_name)['constant']==True):
                ExitFromProgram(f'cannot assign to constant variables')
            
            data_type_of_variable = symbolTable.read(var_name)['datatype']
            id_of_variable = symbolTable.read(var_name)['id']
            expr, data_type_of_assigning_value = self.visit(ctx.expression(0))  

            if(data_type_of_assigning_value!='char' and data_type_of_assigning_value!='str' and data_type_of_assigning_value!=data_type_of_variable):
                ExitFromProgram(f'Cannot assign {data_type_of_assigning_value} to {data_type_of_variable}')

            # self.instructions.append(f'store local {id_of_variable} {data_type_of_variable}')  
            self.instructions.append(f'pop local {id_of_variable} {data_type_of_variable.upper()}')  

        # (IDENTIFIER assignOp expression ';')
        elif ctx.idOrPointerOrAddrId() and ctx.assignOp() and ctx.expression(0): # a+=3 type statements
            var_name = self.visit(ctx.idOrPointerOrAddrId())[1]
            if(not symbolTable.read(var_name)):
                ExitFromProgram("cannot assign to undeclared variable") 
            if(symbolTable.read(var_name)['constant']==True):
                ExitFromProgram(f'cannot assign to constant variables')

            op = ctx.assignOp().getText()  
            
            data_type_of_variable = symbolTable.read(var_name)['datatype']
            id_of_variable = symbolTable.read(var_name)['id']

            self.instructions.append(f'push local {id_of_variable} {data_type_of_variable.upper()}')  
            expr, data_type_of_assigning_value = self.visit(ctx.expression(0))  
            if(data_type_of_assigning_value!='char' and data_type_of_assigning_value!='str' and data_type_of_assigning_value!=data_type_of_variable):
                ExitFromProgram(f'Cannot assign {data_type_of_assigning_value} to {data_type_of_variable}')
            
            if op == '+=':
                self.instructions.append('add')  
            elif op == '-=':
                self.instructions.append('sub')  
            elif op == '*=':
                self.instructions.append('mul')  
            elif op == '/=':
                self.instructions.append('div')
            elif op == '%=':
                self.instructions.append('mod') 
            
            # self.instructions.append(f'store local {id_of_variable} {data_type_of_variable}')
            self.instructions.append(f'pop local {id_of_variable} {data_type_of_variable.upper()}')  

        # to be done
        elif ctx.structAssignStmt():
            return self.visit(ctx.structAssignStmt())  
        elif ctx.enumAccessStmt():
            return self.visit(ctx.enumAccessStmt())
        else:
            raise Exception("Unhandled assignment statement type")

    def visitReturnStmt(self, ctx:joiParser.ReturnStmtContext):
        global current_func_name, current_func_return_type, returnStmtFound
        varname_of_return = None
        data_type_of_return = None
        returnStmtFound = True
        if ctx.expression():
            varname_of_return, data_type_of_return = self.visit(ctx.expression())
        # self.instructions.append('RETURN')
        func_name =current_func_name
        return_type = current_func_return_type
        data_type_func_returns = data_type_of_return
        if(return_type=="void" and data_type_func_returns!=None):
            ExitFromProgram(f'You cannot return anything for a void function')
        if(return_type!=data_type_func_returns):
            ExitFromProgram(f'function {func_name} should return {return_type.upper()}, but you are returning {data_type_func_returns}')
             
                # else: #there is no return statement, this is acceptable only if return type is void.. if return type is not void then throw error
                #     if(return_type!="void"):
                #         ExitFromProgram(f'function {func_name} must return {return_type.upper()} type. Currently you are returning nothing')
        self.instructions.append('return')
        return varname_of_return, data_type_of_return

    # def visitIfStmt(self, ctx: joiParser.IfStmtContext):
    #     varname_of_condition, data_type_of_condition = self.visit(ctx.condition()) #varname of condition is not useful in this case for big expressions.. can be useful only if condition is singel variable
    #     #however we don't use the above things.. they are there only for future purposes
    #     global elseifqueue, elseifq, elseq, elseifqueue, ifq, elsequeue
    #     k=0
    #     if(len(ctx.elseIfStmt())>0):
    #         k=1
    #         for i in range(elseifq+len(ctx.elseIfStmt())-1, elseifq-1, -1):
    #             elseifqueue.append(i)
    #         elseifq+=len(ctx.elseIfStmt())
    #     if(ctx.elseStmt()):
    #         k=1
    #         elsequeue.append(elseq)
    #         elseq+=1

    #     if(k):
    #         if(len(elseifqueue)>0):
    #             self.instructions.append(f'JZ, elseif_{elseifqueue[-1]}')
    #         elif(elsequeue):
    #             self.instructions.append(f'JZ, else_{elsequeue[-1]}')
    #     else:
    #         self.instructions.append(f'JZ, goto end_if_{ifqueue[-1]}')

    #     self.visit(ctx.statements())
    #     self.instructions.append(f'goto end_if_{ifqueue[-1]}')

    #     for elseifstmt in ctx.elseIfStmt():
    #         self.instructions.append(f'elseif_{elseifqueue[-1]}:')
    #         elseifqueue.pop()
    #         self.visit(elseifstmt)
    #         self.instructions.append(f'goto end_if_{ifqueue[-1]}')

    #     if(ctx.elseStmt()):
    #         self.instructions.append(f'else_{elsequeue[-1]}:')
    #         self.visit(ctx.elseStmt())
    #         elsequeue.pop()
    #     self.instructions.append(f'end_if_{ifqueue[-1]}:')
    #     ifqueue.pop()

    def visitIfStmt(self, ctx: joiParser.IfStmtContext):
        global ifqueue
        current_if_index = len(ifqueue)
        ifqueue.append(current_if_index)

        self.visit(ctx.condition())
        self.instructions.append(f'if-goto IF_TRUE{current_if_index}')
        self.instructions.append(f'goto IF_FALSE{current_if_index}')
        self.instructions.append(f'label IF_TRUE{current_if_index}')
        self.visit(ctx.statements())
        self.instructions.append(f'goto IF_END{current_if_index}')

        for elseifstmt in ctx.elseIfStmt():
            self.instructions.append(f'label IF_FALSE{current_if_index}')
            self.visit(elseifstmt.condition())
            current_if_index += 1
            self.instructions.append(f'if-goto IF_TRUE{current_if_index}')
            self.instructions.append(f'goto IF_FALSE{current_if_index}')
            self.instructions.append(f'label IF_TRUE{current_if_index}')
            self.visit(elseifstmt.statements())
            self.instructions.append(f'goto IF_END{ifqueue[-1]}')

        if ctx.elseStmt():
            self.instructions.append(f'label IF_FALSE{current_if_index}')
            self.visit(ctx.elseStmt())
            self.instructions.append(f'goto IF_END{ifqueue[-1]}')
        else:
            self.instructions.append(f'label IF_FALSE{current_if_index}')

        self.instructions.append(f'label IF_END{ifqueue[-1]}')
        ifqueue.pop()

    # def visitElseIfStmt(self, ctx: joiParser.ElseIfStmtContext):
    #     varname_of_condition, data_type_of_condition = self.visit(ctx.condition())
    #     global elseifqueue, elseifq, elseq, elseifqueue, ifq, elsequeue
    #     if(elseifqueue):
    #         self.instructions.append(f'JZ, elseif_{elseifqueue[-1]}')
    #     else:
    #         self.instructions.append(f'JZ, else_{elsequeue[-1]}')
    #     self.visit(ctx.statements())

    # def visitElseStmt(self, ctx: joiParser.ElseStmtContext):
    #     self.visit(ctx.statements())


    # def visitWhileStmt(self, ctx: joiParser.WhileStmtContext):
    #     global loopqueue, whileq, BreakOrContinueWhichLoop
    #     BreakOrContinueWhichLoop.append(f'while_{loopqueue[-1]}')
    #     self.instructions.append(f'while_{loopqueue[-1]}:')
    #     varname_of_condition, data_type_of_condition = self.visit(ctx.condition())
    #     self.instructions.append(f'JZ, end_while_{loopqueue[-1]}')
    #     self.visit(ctx.statements())
    #     self.instructions.append(f'JMP, while_{loopqueue[-1]}')
    #     self.instructions.append(f'end_while_{loopqueue[-1]}:')
    #     loopqueue.pop()
    #     BreakOrContinueWhichLoop.pop()

    def visitWhileStmt(self, ctx: joiParser.WhileStmtContext):
        global loopqueue, BreakOrContinueWhichLoop, label_counter
        current_loop_label = f"#L{label_counter}"
        label_counter +=1
        loopqueue.append(current_loop_label)
        BreakOrContinueWhichLoop.append(current_loop_label)
        self.instructions.append(f"LABEL {current_loop_label}")
        varname_of_condition, data_type_of_condition = self.visit(ctx.condition())
        self.instructions.append(f"JZ, goto end_{current_loop_label}")
        self.visit(ctx.statements())
        self.instructions.append(f"goto {current_loop_label}")
        self.instructions.append(f"LABEL end_{current_loop_label}")
        loopqueue.pop()
        BreakOrContinueWhichLoop.pop()


    # def visitDoWhileStmt(self, ctx: joiParser.DoWhileStmtContext):
    #     global dowhilequeue, dowhileq, BreakOrContinueWhichLoop
    #     BreakOrContinueWhichLoop.append(f'do_while_{dowhilequeue[-1]}')
    #     self.instructions.append(f'do_while_{dowhilequeue[-1]}:')
    #     self.visit(ctx.statements())
    #     varname_of_condition, data_type_of_condition = self.visit(ctx.condition())
    #     self.instructions.append(f'JZ, end_do_while_{dowhilequeue[-1]}')
    #     self.instructions.append(f'JMP, do_while_{dowhilequeue[-1]}')
    #     self.instructions.append(f'end_do_while_{dowhilequeue[-1]}:')
    #     dowhilequeue.pop()
    #     BreakOrContinueWhichLoop.pop()

    def visitDoWhileStmt(self, ctx: joiParser.DoWhileStmtContext):
        global loopqueue, BreakOrContinueWhichLoop, label_counter
        current_loop_label = f"#L{label_counter}"
        label_counter+=1
        loopqueue.append(current_loop_label)
        BreakOrContinueWhichLoop.append(current_loop_label)
        self.instructions.append(f"LABEL {current_loop_label}")
        self.visit(ctx.statements())
        varname_of_condition, data_type_of_condition = self.visit(ctx.condition())
        self.instructions.append(f"JZ, goto end_{current_loop_label}")
        self.instructions.append(f"goto {current_loop_label}")
        self.instructions.append(f"LABEL end_{current_loop_label}")
        loopqueue.pop()
        BreakOrContinueWhichLoop.pop()

    def visitSwitchStmt(self, ctx: joiParser.SwitchStmtContext):
        global switchq, switchqueue, caseq, casequeue
        varname_of_switch_expression, data_type_of_switch_expression = self.visit(ctx.expression())
        for i in range(caseq+len(ctx.caseStmt())-1, caseq-1, -1):
            casequeue.append(i)
        caseq+=len(ctx.caseStmt())

        for case in ctx.caseStmt():
            self.instructions.append(f'case_{casequeue[-1]}:')
            casequeue.pop()
            varname_of_case_expression, data_type_of_case_expression = self.visit(case)
            #check if case_expression and switch expression have same_datatypes.. if not then we cannot compare them in the first place so exit the program
            # print(data_type_of_switch_expression, data_type_of_case_expression)
            if(data_type_of_case_expression != data_type_of_switch_expression):
                ExitFromProgram(f'cannot compare switch expression with the case expression due to mismatching datatypes\n{data_type_of_switch_expression} in switch is compared to {data_type_of_case_expression} in case')

        self.instructions.append(f'default_{switchqueue[-1]}:')
        if(ctx.defaultStmt()):
            self.visit(ctx.defaultStmt())
        self.instructions.append(f'end_switch_{switchqueue[-1]}:')
        switchqueue.pop()
            
    def visitCaseStmt(self, ctx: joiParser.CaseStmtContext):
        global casequeue, switchqueue
        varname_of_expression, data_type_of_expression = self.visit(ctx.expression())
        if(casequeue):
            self.instructions.append(f'JZ, case_{casequeue[-1]}')
        else:
            self.instructions.append(f'JZ, default_{switchqueue[-1]}')
        self.visit(ctx.statements())
        self.instructions.append(f'goto end_switch_{switchqueue[-1]}')

        return varname_of_expression, data_type_of_expression # during switch case we will compare this datatype with switch expr datatype and decide if they can be evaluated at all

    def visitDefaultStmt(self, ctx: joiParser.DefaultStmtContext):
        self.visit(ctx.statements())

    # def visitForStmt(self, ctx: joiParser.ForStmtContext):
    #     global forq, forqueue, BreakOrContinueWhichLoop
    #     BreakOrContinueWhichLoop.append(f'for_{forqueue[-1]}')
    #     self.visit(ctx.forInit())
    #     self.instructions.append(f'for_{forqueue[-1]}:')
    #     if(ctx.condition()):
    #         self.visit(ctx.condition())
    #         self.instructions.append(f'JZ, end_for_{forqueue[-1]}')
    #     self.visit(ctx.statements())
    #     # self.visit(ctx.forUpdate())
    #     self.instructions.append(f'JMP, for_{forqueue[-1]}')
    #     self.instructions.append(f'end_for_{forqueue[-1]}:')
    #     forqueue.pop()
    #     BreakOrContinueWhichLoop.pop()

    def visitForStmt(self, ctx: joiParser.ForStmtContext):
        global forq, loopqueue, BreakOrContinueWhichLoop, label_counter
        current_loop_label = f"#L{label_counter}"
        label_counter+=1
        loopqueue.append(current_loop_label)
        BreakOrContinueWhichLoop.append(current_loop_label)
        self.visit(ctx.forInit())
        self.instructions.append(f'LABEL {current_loop_label}')
        if ctx.condition():
            self.visit(ctx.condition())
            self.instructions.append(f'JZ, goto end_{current_loop_label}')
        self.visit(ctx.statements())
        self.visit(ctx.forUpdate())
        self.instructions.append(f'goto {current_loop_label}')
        self.instructions.append(f'LABEL end_{current_loop_label}')
        loopqueue.pop()
        BreakOrContinueWhichLoop.pop()

    def visitForInit(self, ctx: joiParser.ForInitContext):
        if(ctx.assignStmt()):
            self.visit(ctx.assignStmt())
        elif(ctx.declarationStmt()):
            for declaration in ctx.declarationStmt():
                self.visit(declaration)

    def visitForUpdate(self, ctx: joiParser.ForUpdateContext):
        _, __ = self.visit(ctx.expression())
        ##No need for returning these values here.. we don't have any use with their values or datatypes
        ## because this is just 'for loop' update.. there is nothing we can do with them







    def visitCondition(self, ctx: joiParser.ConditionContext):
        return self.visit(ctx.expression())

    def visitArithmeticOp(self, ctx:joiParser.ArithmeticOpContext):
        op = ctx.getText()
        if op == '+':
            self.instructions.append('add')
        elif op == '-':
            self.instructions.append('sub')
        elif op == '*':
            self.instructions.append('mul')
        elif op == '/':
            self.instructions.append('div')
        elif op == '%':
            self.instructions.append('mod')
                
    def visitComparisonOp(self, op):
        if op == '==':
            operation = 'eq'
        elif op == '!=':
            operation = 'neq'
        elif op == '>':
            operation = 'gt'
        elif op == '<':
            operation = 'lt'
        elif op == '>=':
            operation = 'gte'
        elif op == '<=':
            operation = 'lte'
        
        self.instructions.append(operation)
        return operation 



            
    def visitStructDef(self, ctx: joiParser.StructDefContext):
        struct_name = ctx.IDENTIFIER().getText()
        self.instructions.append(f'STRUCT_{struct_name}')
        if symbolTable.read(struct_name):
            ExitFromProgram(f"Struct '{struct_name}' already defined.")
        symbolTable.create(name=struct_name, symbol_type='struct', scope='ytd')

        for declaration in ctx.declarationStmt():
            self.visit(declaration)
        self.instructions.append(f'STRUCT_END_{struct_name}')
            
    def visitStructDeclarationStmt(self, ctx: joiParser.StructDeclarationStmtContext):
        struct_name = ctx.IDENTIFIER(0).getText()
        var_name = ctx.IDENTIFIER(1).getText()
        if symbolTable.read(var_name):
            ExitFromProgram(f"Variable '{var_name}' already declared.")
        if not symbolTable.read(struct_name):
            ExitFromProgram(f"Struct '{struct_name}' is not defined.")
        symbolTable.create(name=var_name, symbol_type='struct_variable', scope='ytd', datatype=struct_name)
        self.instructions.append(f'DECLARE {struct_name} {var_name}')
        
    def visitStructAccessStmt(self, ctx: joiParser.StructAccessStmtContext):
        struct_var = ctx.IDENTIFIER(0).getText()
        member = ctx.IDENTIFIER(1).getText()
        struct_info = symbolTable.read(struct_var)
        # if not struct_info or struct_info['type'] != 'struct_variable':
        #     ExitFromProgram(f"'{struct_var}' is not a struct variable.")
        member_info = symbolTable.read(f"{member}")
        if not member_info:
            ExitFromProgram(f"Struct '{struct_info['datatype']}' has no member '{member}'.")
        # self.instructions.append(f'PUSH {struct_var}')
        # self.instructions.append(f'PUSH_FIELD {member}')
        self.instructions.append(f'PUSH {struct_var}.{member}')
        return struct_var, member
        
        
    def visitStructAssignStmt(self, ctx: joiParser.StructAssignStmtContext):
        # if struct_var_name is not None:  
        total_expressions = len(ctx.expression())
        
        if(total_expressions>1):
            self.instructions.append(f'ARR_INDEX START')
            for i in range(0, total_expressions-1):
                index, index_data_type = self.visit(ctx.expression(i))
                if(index_data_type!='int'):
                    ExitFromProgram(f'array cannot be accessed with {index_data_type} in []. Please use integers') 
            self.instructions.append(f'ARR_INDEX END')
            struct_var_name, struct_var_member = self.visit(ctx.structAccessStmt())
            # self.instructions.append(f'PUSH_ARRAY {struct_var_name}.{struct_var_member}')  
        else:
            # self.instructions.append(f'PUSH {struct_var_name}') ## this might be correct but for simplicity in understanding writing like below
            # self.instructions.append(f'PUSH_FIELD {struct_var_member}')
            struct_var_name, struct_var_member = self.visit(ctx.structAccessStmt())
            # self.instructions.append(f'PUSH {struct_var_name}.{struct_var_member}')
            
        value_to_assign, data_type_of_value_to_assign = self.visit(ctx.expression(total_expressions-1)) #this is the value to assign
        data_type_of_member = symbolTable.read(struct_var_member)['datatype']

        if(ctx.assignOp()):
            #assignOp must work only on integers or floats
            op = ctx.assignOp().getText()                
            if op == '+=':
                self.instructions.append('add')  
            elif op == '-=':
                self.instructions.append('sub')  
            elif op == '*=':
                self.instructions.append('mul')  
            elif op == '/=':
                self.instructions.append('div')
            elif op == '%=':
                self.instructions.append('mod') 

            if((data_type_of_member!='int' or data_type_of_value_to_assign!='int') and (data_type_of_member!='float' or data_type_of_value_to_assign!='float')):
                ExitFromProgram(f'can perform {op} operation only int and floats.\n{struct_var_member} is of {data_type_of_member} and you are trying to do {op} with {data_type_of_value_to_assign}')
            

        if(data_type_of_value_to_assign!=data_type_of_member):
            ExitFromProgram(f'cannot assign {data_type_of_value_to_assign} to {data_type_of_member} {struct_var_name}.{struct_var_member}')
        
        if(total_expressions>1):
            self.instructions.append(f'STORE {data_type_of_member} {struct_var_name}.{struct_var_member}')
            self.instructions.append(f'POP_ARRAY')
        else:
            self.instructions.append(f'STORE {data_type_of_member} {struct_var_name}.{struct_var_member}')
            self.instructions.append(f'POP {struct_var_name}.{struct_var_member}')

    
    def visitEnumDef(self, ctx: joiParser.EnumDefContext):
        enum_name = ctx.IDENTIFIER(0).getText()
        constants = ctx.IDENTIFIER()[1:]
        if symbolTable.read(enum_name):
            ExitFromProgram(f"Enum '{enum_name}' already defined.")
        symbolTable.create(name=enum_name, symbol_type='enum', scope='ytd')
    

        for idx, constant in enumerate(constants):
            const_name = constant.getText()
            symbolTable.create(name=const_name, symbol_type='const', scope='ytd', value=idx) #instead PUSH idx, DECLARE_CONST const_name,                                                                                         
            self.instructions.append(f'DECLARE_CONST {const_name} = {idx}') #STORE const_name, POP const_name



    def visitEnumDeclarationStmt(self, ctx: joiParser.EnumDeclarationStmtContext):
        enum_name = ctx.IDENTIFIER(0).getText()
        member_name = ctx.IDENTIFIER(1).getText()
        if not symbolTable.read(enum_name):
            ExitFromProgram(f"Enum '{enum_name}' is not defined.")

        assigned_value = ctx.IDENTIFIER(2).getText() if ctx.IDENTIFIER(2) else None

        if assigned_value:
            value = int(assigned_value)
            symbolTable.create(name=f"{enum_name}.{member_name}", symbol_type='const', scope='ytd', value=value)
            self.instructions.append(f"DECLARE_CONST {enum_name}.{member_name} = {value}")
        else:
            symbolTable.create(name=f"{enum_name}.{member_name}", symbol_type='const', scope='ytd')
            self.instructions.append(f"DECLARE_CONST {enum_name}.{member_name}")
    
    def visitEnumAccessStmt(self, ctx: joiParser.EnumAccessStmtContext):
        enum_member = ctx.IDENTIFIER(0).getText()
        assigned_value = ctx.IDENTIFIER(1).getText()

        if not symbolTable.read(enum_member):
            ExitFromProgram(f"Enum member '{enum_member}' is not defined.")

        value = int(assigned_value) 
        symbolTable.update(enum_member, value=value)
        self.instructions.append(f"STORE {enum_member} = {value}")
        
    def visitIncludeStmt(self, ctx: joiParser.IncludeStmtContext):
        header_content = self.visit(ctx.header())
        if header_content:
            self.instructions.append(f"lib {header_content}.jvm")
        return None

    def visitHeader(self, ctx: joiParser.HeaderContext):
        identifier = ctx.IDENTIFIER().getText()  
        # if ctx.IDENTIFIER(1):  
        #     extension = ctx.IDENTIFIER(1).getText()
        #     return f"{identifier}"
        return identifier  


    def visitMainFunction(self, ctx:joiParser.MainFunctionContext):
        self.instructions.append('function joi 0 INT')  
        self.visit(ctx.statements())  
        self.visit(ctx.expression())  
        self.instructions.append('return')  
        self.instructions.append('halt')  
        global joiFuncVisited
        joiFuncVisited = True
        # symbolTable.display()
        # print("\nOPTIMISED CODE\n")
        self.optimised_instructions = self.optimise_unused_functions()
        # optimised_code_instruction_form = ""
        # for i in optimised_code_array_form:
        #     optimised_code_instruction_form.append(i)
        # print(optimised_code_instruction_form)
        

    def optimise_unused_functions(self):
        unused_functions = [
        name for name, attributes in symbolTable.table.items()
        if attributes['type'] == 'function' and not attributes['functioncalled']
        ]
    
        optimized_instructions = self.instructions[:]
    
        for function in unused_functions:
            try:
                # Find the line where the function appears
                start_index = next(i for i, line in enumerate(optimized_instructions) if function in line)
                
                # Find the first 'return' after the function's line
                end_index = next(
                    i for i in range(start_index + 1, len(optimized_instructions)) if 'return' in optimized_instructions[i] or 'return_' in optimized_instructions[i]
                )
                
                # Remove lines between start_index and end_index
                optimized_instructions = (
                    optimized_instructions[:start_index] + optimized_instructions[end_index + 1:]
                )
            except StopIteration:
                # If no 'return' is found or the function name isn't in the instructions, skip
                continue
    
        return optimized_instructions