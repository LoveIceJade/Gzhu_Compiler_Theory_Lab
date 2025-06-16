import sys

# LR0项目结构
class Item:
    def __init__(self, p, d):
        self.production = p  # 产生式的编号
        self.dot_pos = d        # 点的位置
    
    # 重载<
    def __lt__(self, other):
        if self.production != other.production:
            return self.production < other.production
        return self.dot_pos < other.dot_pos
    
    # 重载==
    def __eq__(self, other):
        return self.production == other.production and self.dot_pos == other.dot_pos
    
    # 为了在set中使用，需要实现hash方法
    def __hash__(self):
        return hash((self.production, self.dot_pos))

# 产生式结构
class Production:
    def __init__(self, l, r):
        self.left = l    # 左部
        self.right = r  # 右部

# LR0分析器
class LR0Parser:
    def __init__(self):
        # 需要保持顺序、随机访问、按添加顺序维护，所以使用数组
        self.productions = []  # 产生式集合
        self.itemSets = []     # 项目集族
        
        # 需要唯一性和高速查找功能，所以使用集合
        self.terminals = {"$"}    # 终结符集合
        self.nonterminals = set()  # 非终结符集合
        
        self.gotoTable = {}    # goto表
        self.startSymbol = ""   # 开始符号
        self.augmentedStart = "" # 增广开始符号
    
    # 解析输入的产生式
    def parseProduction(self, input_str):
        result = []
        
        arrowPos = input_str.find("->")
        if arrowPos == -1:  # 没找到"->"
            print(f"错误：产生式格式不正确，请输入'->'：{input_str}")
            return result
        
        # 提取左部并去除首尾空格
        left = input_str[:arrowPos].strip()
        
        if not left:
            print("错误：产生式左部为空")
            return result
        
        # 提取右部并去除首尾空格
        rightStr = input_str[arrowPos+2:].strip()
        
        # 按 | 分割多个右部
        alternatives = rightStr.split('|')
        
        for alternative in alternatives:
            # 去除空格
            alternative = alternative.strip()
            
            # 处理空产生式
            if alternative == "ε":
                right = []
            else:
                # 分割右部符号（按空格分割）
                right = alternative.split()
            
            result.append((left, right))
        
        return result
    
    # 输入文法
    def inputGrammar(self):
        print("请输入文法产生式（每行一个，空行结束）:")
        print("格式: A -> B C 或 A -> B C | D E (多选择) 或 A -> ε ")
        print("示例:")
        print("E -> E + T | T")
        print("T -> T * F | F")
        print("F -> ( E ) | id")
        print()
        
        inputProductions = []
        
        while True:
            line = input()
            if not line:
                break
            
            # 解析可能包含多个选择的产生式
            parserProds = self.parseProduction(line)
            
            if parserProds:
                for prod in parserProds:
                    inputProductions.append(prod)
                    self.nonterminals.add(prod[0])
                    
                    # 收集终结符
                    for symbol in prod[1]:
                        if symbol not in self.nonterminals:
                            # 先假设为终结符，后面调整
                            self.terminals.add(symbol)
        
        if not inputProductions:
            print("未产生任何产生式！")
            return
        
        # 调整终结符集合（移除非终结符）
        for nt in self.nonterminals:
            if nt in self.terminals:
                self.terminals.remove(nt)
        
        # 设置开始符号为第一个产生式的左部
        self.startSymbol = inputProductions[0][0]
        self.augmentedStart = self.startSymbol + "'"
        
        # 构建增广文法
        self.productions.clear()
        
        # 添加增广开始式 S' -> S
        augmentedRight = [self.startSymbol]
        self.productions.append(Production(self.augmentedStart, augmentedRight))
        self.nonterminals.add(self.augmentedStart)
        
        # 添加原始产生式
        for prod in inputProductions:
            self.productions.append(Production(prod[0], prod[1]))
        
        print("文法输入完成！")
        self.printGrammarInfo()
    
    # 打印文法信息
    def printGrammarInfo(self):
        print("\n=== 文法信息 ===")
        print(f"开始符号：{self.startSymbol}")
        print(f"增广开始符：{self.augmentedStart}")
        
        print("\n非终结符：{", end="")
        print(",".join(self.nonterminals), end="")
        print(" }")
        
        print("\n产生式：")
        for i, prod in enumerate(self.productions):
            print(f"{i}：{prod.left}->", end="")
            if not prod.right:
                print("ε", end="")
            else:
                print(" ".join(prod.right), end="")
            print()
        print()
    
   # 闭包计算
    def closure(self, items):
        result = items.copy()
        changed = True
    
        # 遍历，直至没有新的产生式加入
        while changed:
            changed = False
            newItems = set()
        
            temp = list(result)
            for item in temp:
                prod = self.productions[item.production]
            
                # 如果点不在最右端
                if item.dot_pos < len(prod.right):
                    nextSymbol = prod.right[item.dot_pos]
                
                    # 如果点后面是非终结符
                    if nextSymbol in self.nonterminals:
                        # 找到所有以该非终结符为左部的产生式
                        for i in range(len(self.productions)):
                            if self.productions[i].left == nextSymbol:
                                newItem = Item(i, 0)
                                if newItem not in result:
                                    newItems.add(newItem)
                                    changed = True
        
            result.update(newItems)
    
        return result
    
    # 计算GOTO(I,X)
    def gotoSet(self, items, symbol):
        """计算项目集I读入符号X后的转移项目集
        
        参数:
            items: 项目集I
            symbol: 输入符号X
            
        返回:
            转移后的项目集
        """
        result = set()
        
        for item in items:
            # 检查产生式索引是否有效
            if not (0 <= item.production < len(self.productions)):
                continue  # 跳过无效的产生式索引
                
            prod = self.productions[item.production]
            
            # 如果点后面是symbol，则将点向右移动一位
            if item.dot_pos < len(prod.right) and prod.right[item.dot_pos] == symbol:
                newItem = Item(item.production, item.dot_pos + 1)
                result.add(newItem)
        
        # 对结果项目集进行闭包操作
        return self.closure(result)
    
    # 构造LR0项目集族
    def buildItemSets(self):
        self.itemSets.clear()
        self.gotoTable.clear()
        
        # 初始项目集I0
        I0 = {Item(0, 0)}  # S' -> .S
        I0 = self.closure(I0)
        self.itemSets.append(I0)
        
        workList = [0]
        
        while workList:
            # 从workList中取出第一个元素
            currentIndex = workList.pop(0)
            currentSet = self.itemSets[currentIndex]
            
            # 收集所有可能的转移符号
            symbols = set()
            for item in currentSet:
                prod = self.productions[item.production]
                if item.dot_pos < len(prod.right):
                    symbols.add(prod.right[item.dot_pos])
            
            # 对每个符号计算GOTO
            for symbol in symbols:
                gotoResult = self.gotoSet(currentSet, symbol)
                
                if gotoResult:
                    # 查找是否已存在相同的项目集
                    targetIndex = -1
                    for i, itemSet in enumerate(self.itemSets):
                        if itemSet == gotoResult:
                            targetIndex = i
                            break
                    
                    if targetIndex == -1:
                        # 新的项目集
                        targetIndex = len(self.itemSets)
                        self.itemSets.append(gotoResult)
                        workList.append(targetIndex)
                    
                    # 记录转移
                    self.gotoTable[(currentIndex, symbol)] = targetIndex
        
        print("buildItemSets函数成功运行！")
    
    # 打印项目
    def printItem(self, item):
        """返回项目的字符串表示"""
        prod = self.productions[item.production]
        result = f"{prod.left}->"
        
        if not prod.right:
            if item.dot_pos == 0:
                result += ".ε"
            else:
                result += "ε."
        else:
            for i in range(len(prod.right)):
                if i == item.dot_pos:
                    result += "."
                result += prod.right[i]
                if i < len(prod.right) - 1:
                    result += " "
            
            if item.dot_pos == len(prod.right):
                result += "."
        
        return result
    
    # 打印项目集族
    def printItemSets(self):
        print("\n=== LR0项目集族 ===")
        for i, itemSet in enumerate(self.itemSets):
            print(f"I{i}：")
            for item in itemSet:
                print(f"    {self.printItem(item)}")
            print()
    
    # 计算First集合
    def computeFirstSets(self):
        """计算所有非终结符的First集合
        
        First(X)表示非终结符X可以推导出的所有串的首符号集合
        """
        # 初始化所有非终结符的First集合为空集
        self.first_sets = {nt: set() for nt in self.nonterminals}
        
        # 添加所有终结符的First集合，First(a) = {a}
        for t in self.terminals:
            self.first_sets[t] = {t}
        
        # 添加空串的First集合，First(ε) = {ε}
        self.first_sets['ε'] = {'ε'}
        
        changed = True
        while changed:
            changed = False
            
            # 遍历所有产生式
            for prod in self.productions:
                # 获取产生式左侧的非终结符
                nt = prod.left
                
                # 如果右侧为空，则将ε加入First集合
                if len(prod.right) == 0:
                    if 'ε' not in self.first_sets[nt]:
                        self.first_sets[nt].add('ε')
                        changed = True
                    continue
                
                # 计算右侧序列的First集合
                first_of_right = self.getFirstOfSequence(prod.right)
                
                # 将计算得到的First集合加入到非终结符的First集合中
                for symbol in first_of_right:
                    if symbol not in self.first_sets[nt]:
                        self.first_sets[nt].add(symbol)
                        changed = True
    
    # 计算符号序列的First集合
    def getFirstOfSequence(self, sequence):
        """计算符号序列的First集合
        
        参数:
            sequence: 符号序列
            
        返回:
            符号序列的First集合
        """
        if not sequence:  # 空序列
            return {'ε'}
        
        result = set()
        all_derive_epsilon = True
        
        # 遍历序列中的每个符号
        for symbol in sequence:
            # 如果符号不能推导出ε，则后续符号不再考虑
            if 'ε' not in self.first_sets[symbol]:
                all_derive_epsilon = False
                result.update(self.first_sets[symbol])
                break
            
            # 将除ε外的所有符号加入结果集
            result.update(self.first_sets[symbol] - {'ε'})
        
        # 如果所有符号都能推导出ε，则将ε加入结果集
        if all_derive_epsilon:
            result.add('ε')
        
        return result

    # 计算Follow集合
    def computeFollowSets(self):
        """计算所有非终结符的Follow集合
        
        Follow(A)表示在所有句型中紧跟在非终结符A后面的终结符集合
        """
        # 初始化所有非终结符的Follow集合为空集
        self.follow_sets = {nt: set() for nt in self.nonterminals}
        
        # 将#加入到开始符号的Follow集合中
        self.follow_sets[self.startSymbol].add('#')
        
        changed = True
        while changed:
            changed = False
            
            # 遍历所有产生式
            for prod in self.productions:
                # 获取产生式左侧的非终结符
                A = prod.left
                
                # 遍历产生式右侧的每个位置
                for i in range(len(prod.right)):
                    B = prod.right[i]
                    
                    # 如果B是非终结符
                    if B in self.nonterminals:
                        # 计算B后面的符号序列的First集合
                        beta = prod.right[i+1:] if i+1 < len(prod.right) else []
                        first_of_beta = self.getFirstOfSequence(beta)
                        
                        # 将First(β) - {ε}加入到Follow(B)中
                        for symbol in first_of_beta - {'ε'}:
                            if symbol not in self.follow_sets[B]:
                                self.follow_sets[B].add(symbol)
                                changed = True
                        
                        # 如果ε在First(β)中，或者B是产生式右侧的最后一个符号
                        # 则将Follow(A)加入到Follow(B)中
                        if 'ε' in first_of_beta or not beta:
                            for symbol in self.follow_sets[A]:
                                if symbol not in self.follow_sets[B]:
                                    self.follow_sets[B].add(symbol)
                                    changed = True

    # 检查冲突
    def checkConflict(self, useSLR1=False):
        """检查语法是否存在冲突
        参数:
            useSLR1: 是否使用SLR(1)分析方法检查冲突
        返回:
            如果存在冲突，返回True；否则返回False
        """
        hasConflict = False
        
        # 遍历所有项目集
        for i, items in enumerate(self.itemSets):
            # 检查是否有移进-归约冲突或归约-归约冲突
            reduce_items = []
            shift_symbols = set()
            
            # 收集所有归约项和移进符号
            for item in items:
                prod = self.productions[item.production]
                
                # 归约项
                if item.dot_pos == len(prod.right):
                    reduce_items.append(item)
                # 移进项
                elif item.dot_pos < len(prod.right):
                    shift_symbols.add(prod.right[item.dot_pos])
            
            # 检查冲突
            if reduce_items:
                for reduce_item in reduce_items:
                    prod = self.productions[reduce_item.production]
                    
                    # 对于SLR(1)，只在Follow集中的终结符上执行归约
                    if useSLR1:
                        reduce_terminals = self.follow_sets[prod.left] & self.terminals
                    else:
                        reduce_terminals = self.terminals
                    
                    # 检查移进-归约冲突
                    sr_conflicts = shift_symbols & reduce_terminals
                    if sr_conflicts:
                        hasConflict = True
                        if not useSLR1:
                            print(f"\n移进-归约冲突在状态 {i}:")
                            print(f"  项目: {self.printItem(reduce_item)}")
                            print(f"  冲突符号: {', '.join(sorted(sr_conflicts))}")
                    
                    # 检查归约-归约冲突
                    for other_reduce in reduce_items:
                        if other_reduce != reduce_item:
                            other_prod = self.productions[other_reduce.production]
                            
                            # 对于SLR(1)，检查Follow集是否有交集
                            if useSLR1:
                                rr_conflicts = self.follow_sets[prod.left] & self.follow_sets[other_prod.left] & self.terminals
                            else:
                                rr_conflicts = self.terminals  # LR(0)总是有规约-规约冲突
                            
                            if rr_conflicts and not useSLR1:
                                hasConflict = True
                                print(f"\n归约-归约冲突在状态 {i}:")
                                print(f"  项目1: {self.printItem(reduce_item)}")
                                print(f"  项目2: {self.printItem(other_reduce)}")
                                print(f"  冲突符号: {', '.join(sorted(rr_conflicts))}")
        
        return hasConflict

    # 打印Follow集合
    def printFollowSets(self):
        # 打印所有非终结符的Follow集合
        print("\nFollow集:")
        for nt in sorted(self.nonterminals):
            follow_str = ', '.join(sorted(self.follow_sets[nt]))
            print(f"FOLLOW({nt}) = {{ {follow_str} }}")
        print()
    
    # 构建Action表
    def buildActionTable(self, useSLR1=False):
        """构建LR分析表中的Action部分
        参数:
            use_slr1: 是否使用SLR(1)分析方法构建Action表
            
        返回:
            构建的Action表
        """
        # 确保已计算First和Follow集
        if useSLR1 and not hasattr(self, 'follow_sets'):
            self.computeFirstSets()
            self.computeFollowSets()
        
        # 初始化Action表
        self.actionTable = {}
        
        # 遍历所有项目集
        for i, items in enumerate(self.itemSets):
            self.actionTable[i] = {}
            
            # 处理每个项目
            for item in items:
                prod = self.productions[item.production]
                
                # 如果是移进项
                if item.dot_pos < len(prod.right) and prod.right[item.dot_pos] in self.terminals:
                    symbol = prod.right[item.dot_pos]
                    next_state = self.gotoTable.get((i, symbol))
                    
                    if next_state is not None:
                        # 添加移进动作
                        self.actionTable[i][symbol] = ('shift', next_state)
                
                # 如果是归约项
                elif item.dot_pos == len(prod.right):
                    # 如果是接受项
                    if prod.left == self.augmentedStart and len(prod.right) == 1 and prod.right[0] == self.startSymbol:
                        self.actionTable[i]['#'] = ('accept', None)
                    else:
                        # 对于SLR(1)，只在Follow集中的终结符上执行归约
                        if useSLR1:
                            reduce_terminals = self.follow_sets[prod.left] & self.terminals
                            reduce_terminals.add('#')  # 添加结束符
                        else:
                            reduce_terminals = self.terminals | {'#'}  # 所有终结符和结束符
                        
                        # 添加归约动作
                        for terminal in reduce_terminals:
                            # 如果已经有移进动作，且是SLR(1)，则有冲突
                            if terminal in self.actionTable[i] and useSLR1:
                                print(f"警告：状态{i}对于符号{terminal}存在冲突")
                            else:
                                self.actionTable[i][terminal] = ('reduce', item.production)
        
        return self.actionTable

    # 打印Action-Goto表
    def printActionGotoTable(self):
        """打印合并的Action-Goto表，包含Action部分和Goto部分"""
        print("\n=== Action-Goto表 ===\n")
        
        # 获取所有终结符，包括结束符#
        terminals = sorted(list(self.terminals)) + ['#']
        
        # 获取所有非终结符（除了增广开始符号）
        nonterminals = [nt for nt in sorted(self.nonterminals) if nt != self.augmentedStart]
        
        # 所有符号（先终结符，后非终结符）
        all_symbols = terminals + nonterminals
        
        # 打印表头
        header = "状态\t" + "\t".join(all_symbols)
        print(header)
        print("-" * len(header.expandtabs()))
        
        # 打印每个状态的动作和转移
        for state in range(len(self.itemSets)):
            row = f"{state}\t"
            
            # 处理所有符号
            for symbol in all_symbols:
                # 终结符：查找Action表
                if symbol in terminals:
                    action = self.actionTable.get(state, {}).get(symbol)
                    if action:
                        action_type, action_value = action
                        if action_type == 'shift':
                            row += f"s{action_value}\t"
                        elif action_type == 'reduce':
                            row += f"r{action_value}\t"
                        elif action_type == 'accept':
                            row += "acc\t"
                        else:
                            row += "\t"
                    else:
                        row += "\t"
                # 非终结符：查找Goto表
                else:
                    if (state, symbol) in self.gotoTable:
                        next_state = self.gotoTable[(state, symbol)]
                        row += f"{next_state}\t"
                    else:
                        row += "\t"
            
            print(row)
        print()
    
    # 运行分析器
    def run(self):
        """运行LR分析器，自动判断文法类型并构建相应的分析表"""
        # 输入文法
        self.inputGrammar()
        
        print("\n构建LR(0)项集族...")
        self.buildItemSets()
        
        # 打印项目集族
        self.printItemSets()
        
        print("\n检查文法是否为LR(0)文法...")
        lr0_conflicts = self.checkConflict(useSLR1=False)
        
        if not lr0_conflicts:
            print("\n该文法是LR(0)文法！")

            self.buildActionTable(useSLR1=False)
    
            print("\nLR(0)分析表:")
            self.printActionGotoTable()
            
        else:
            print("\n该文法不是LR(0)文法，尝试SLR(1)分析...")
            
            print("\n计算First集和Follow集...")
            self.computeFirstSets()
            self.computeFollowSets()
            
            self.printFollowSets()
            
            print("\n检查文法是否为SLR(1)文法...")
            slr1_conflicts = self.checkConflict(useSLR1=True)
            
            if not slr1_conflicts:
                print("\n该文法是SLR(1)文法！")
                print("\n构建SLR(1) Action表...")
                self.buildActionTable(useSLR1=True)
                
                print("\nSLR(1)分析表:")
                self.printActionGotoTable()
                
            else:
                print("\n该文法既不是LR(0)文法也不是SLR(1)文法，需要更强大的分析方法（如LR(1)或LALR(1)）。")
            
        choose = 0
        print("是否输入字符串（是的话输入1,否则输入0）：")
        choose=input();

        if choose:
            # 在构建完分析表后，提示用户输入串进行分析
            print("\n请输入要分析的符号串（各符号之间用空格分隔，例如：id + id * id）：")
            input_string = input()
            lr0parser.parseInput(input_string)
            
        print("程序已退出！")

    # 分析输入串
    def parseInput(self, input_string):
        """使用构建好的分析表对输入串进行语法分析
        
        参数:
            input_string: 要分析的输入串，各符号之间用空格分隔
            
        返回:
            是否接受该输入串
        """
        # 检查是否已经构建了分析表
        if not hasattr(self, 'actionTable') or not hasattr(self, 'gotoTable'):
            print("错误：请先构建分析表！")
            return False
        
        # 将输入串分割成符号列表，并添加结束符号
        symbols = input_string.split()
        symbols.append('#')
        
        # 打印调试信息
        print("\n调试信息：")
        print(f"输入符号列表: {symbols}")
        print(f"终结符集合: {sorted(self.terminals)}")
        print(f"非终结符集合: {sorted(self.nonterminals)}")
        
        # 验证输入符号是否都在终结符集合中
        invalid_symbols = []
        for symbol in symbols[:-1]:  # 不检查结束符号'#'
            if symbol not in self.terminals and symbol not in self.nonterminals:
                invalid_symbols.append(symbol)
        
        if invalid_symbols:
            print(f"错误：输入中包含未定义的符号：{', '.join(invalid_symbols)}")
            print("有效的终结符有：{}".format(', '.join(sorted(self.terminals))))
            return False
        
        # 初始化分析栈和符号指针
        stack = [0]  # 状态栈，初始状态为0
        pointer = 0  # 当前输入符号的指针
        
        print("\n=== 语法分析过程 ===")
        print(f"{'步骤':<5}{'状态栈':<20}{'输入':<20}{'动作':<20}")
        
        step = 1
        while True:
            current_state = stack[-1]  # 当前状态
            current_symbol = symbols[pointer]  # 当前输入符号
            
            # 获取动作
            if current_symbol in self.actionTable.get(current_state, {}):
                action = self.actionTable[current_state][current_symbol]
            else:
                action = None
            
            # 打印当前步骤
            state_stack_str = ' '.join(map(str, stack))
            input_str = ' '.join(symbols[pointer:])
            
            # 根据动作类型执行相应操作
            if action is None:
                print(f"{step:<5}{state_stack_str:<20}{input_str:<20}{'错误：无法识别的符号':<20}")
                print("\n分析结果：拒绝接受该输入串！")
                return False
            
            elif action[0] == 'shift':  # 移进
                next_state = action[1]
                print(f"{step:<5}{state_stack_str:<20}{input_str:<20}{f'移进到状态 {next_state}':<20}")
                stack.append(next_state)
                pointer += 1
            
            elif action[0] == 'reduce':  # 规约
                prod_index = action[1]
                prod = self.productions[prod_index]
                
                # 弹出右部长度个状态
                if prod.right:  # 如果右部不为空
                    pop_count = len(prod.right)
                    for _ in range(pop_count):
                        stack.pop()
                
                # 获取当前栈顶状态
                current_top = stack[-1]
                
                # 查找GOTO表
                if (current_top, prod.left) in self.gotoTable:
                    goto_state = self.gotoTable[(current_top, prod.left)]
                    stack.append(goto_state)
                    
                    # 构造规约产生式的字符串表示
                    right_str = ' '.join(prod.right) if prod.right else 'ε'
                    print(f"{step:<5}{state_stack_str:<20}{input_str:<20}{f'规约：{prod.left} -> {right_str}':<20}")
                else:
                    print(f"{step:<5}{state_stack_str:<20}{input_str:<20}{f'错误：无法找到GOTO({current_top}, {prod.left})':<20}")
                    print("\n分析结果：拒绝接受该输入串！")
                    return False
            
            elif action[0] == 'accept':  # 接受
                print(f"{step:<5}{state_stack_str:<20}{input_str:<20}{'接受':<20}")
                print("\n分析结果：成功接受该输入串！")
                return True
            
            step += 1

if __name__ == "__main__":
    lr0parser = LR0Parser()
    lr0parser.run()
    
