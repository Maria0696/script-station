$stack = []

class Step
  attr_accessor :block

  def initialize(block)
    @block = block
  end
end

class Goto < StandardError
  attr_accessor :step

  def initialize(step)
    super(step)
    @step = step
  end
end

def step(&block)
  $stack.push(Step.new(block))
  block.call
end

def return_previous
  optional_block = $stack.pop
  raise unless optional_block

  $stack.last&.block&.call
end
